#!/usr/bin/env python3
"""Pull each DJ's attributed GoFundMe total, write src/data/djs.ts, commit, push.

Per account: open the saved Playwright profile headless, load a page so the
session refreshes its cookies, then page through GetDonationsFromShares over
HTTP and sum the amounts. Auth is cookie-based - there is no token to pass.

Scoping the query to the campaign slug is what makes the figure exact. The
/account/impact headline is lifetime impact across every fundraiser and
includes the account's own giving, so it drifts; slug-scoped edges don't. See
../../../djcompleaderboard/README.md for the history of that finding.

Each roster entry in accounts.json carries a manual_adjustment - dollars a DJ
raised that this scrape structurally cannot see (a donation made through their
own personal GoFundMe account rather than their campaign link, or a gift that
went straight to the charity's general pool instead of a DJ's own link). That
adjustment is added on top of the scraped total, and its note (if any) is
rendered as a comment above that DJ's line in djs.ts.

    py sync.py            # all accounts, then commit + push
    py sync.py dj01       # one account, for debugging - still writes djs.ts
                           # for everyone else from the last good reading
    py sync.py --no-push  # write djs.ts and commit, but don't push
    py sync.py --dry-run  # print what would change, touch nothing
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

# Windows' console codepage can't always represent names/comments verbatim
# (e.g. the em-dash in djs.ts's header comment). A print() crashing here would
# abort an otherwise-successful run before it gets to commit/push, so status
# output degrades gracefully instead of raising. File I/O elsewhere in this
# script always passes encoding="utf-8" explicitly and is unaffected.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
DATA_DIR = ROOT / "data"
LAST_RUN = DATA_DIR / "last-run.json"
LOCK = DATA_DIR / ".sync.lock"
DJS_TS = REPO / "src" / "data" / "djs.ts"

GRAPHQL = "https://graphql.gofundme.com/graphql"
IMPACT_URL = "https://www.gofundme.com/account/impact"

QUERY = """
query GetDonationsFromShares($fundraiserSlug: ID, $first: Int, $after: String) {
  viewer {
    id
    donationsFromShares(fundraiserSlug: $fundraiserSlug, first: $first, after: $after) {
      edges { node { id amount { amount currencyCode } createdAt name } }
      pageInfo { endCursor hasNextPage }
    }
  }
}
"""

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


# --------------------------------------------------------------------------- public

def campaign_snapshot(slug):
    """Overall campaign total, straight off the public page. No auth needed."""
    req = urllib.request.Request(
        f"https://www.gofundme.com/f/{slug}", headers={"User-Agent": UA}
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    blob = re.search(
        r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S
    )
    apollo = json.loads(blob.group(1))["props"]["pageProps"]["__APOLLO_STATE__"]
    fundraiser = next(
        v for k, v in apollo.items()
        if k.startswith("Fundraiser:") and v.get("slug") == slug
    )
    return round(fundraiser["currentAmount"]["amount"])


# --------------------------------------------------------------------- authenticated

def establish_session(page):
    """Load the impact page so the app refreshes its cookies, and report where we landed.

    GoFundMe's GraphQL calls carry no Authorization header - auth rides on
    cookies, which ctx.request shares with the browser context. So there's no
    token to capture; we only need a live session.
    """
    page.goto(IMPACT_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(6_000)
    return page.url


def donations_for(ctx, slug):
    """Page through every donation attributed to this account for one campaign."""
    out, cursor = [], None
    while True:
        resp = ctx.request.post(
            GRAPHQL,
            headers={
                "content-type": "application/json",
                "origin": "https://www.gofundme.com",
                "referer": "https://www.gofundme.com/",
            },
            data=json.dumps({
                "operationName": "GetDonationsFromShares",
                "query": QUERY,
                # 50 is GoFundMe's hard per-page cap on this field.
                "variables": {"fundraiserSlug": slug, "first": 50, "after": cursor},
            }),
        )
        if not resp.ok:
            raise RuntimeError(f"graphql http {resp.status}: {resp.text()[:200]}")

        body = resp.json()
        if body.get("errors"):
            raise RuntimeError(f"graphql errors: {json.dumps(body['errors'])[:300]}")

        shares = (body.get("data") or {}).get("viewer", {}).get("donationsFromShares")
        if not shares:
            raise RuntimeError(f"no donationsFromShares in response: {json.dumps(body)[:200]}")

        for edge in shares.get("edges") or []:
            node = edge.get("node") or {}
            out.append((node.get("amount") or {}).get("amount", 0))

        info = shares.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return out
        cursor = info.get("endCursor")


def read_account(gofundme_id, slug):
    profile = ROOT / "profiles" / gofundme_id
    if not profile.exists():
        raise RuntimeError("no profile - run login.py for this account")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(profile), headless=True)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            url = establish_session(page)
            # Signed out, GoFundMe redirects to /sign-up - so confirm we reached
            # the impact page rather than testing for any particular bounce URL.
            if not url.startswith(IMPACT_URL):
                raise RuntimeError("session expired - re-run login.py for this account")
            return sum(donations_for(ctx, slug))
        finally:
            ctx.close()


# ------------------------------------------------------------------------ assembling

def previous(config):
    """Last known-good numbers, so a failed scrape never overwrites real data.

    Normally this is last-run.json from the previous sync. Before that file
    exists at all - the very first run, e.g. before login.py has ever signed
    an account in - fall back to whatever is currently committed in djs.ts.
    Without this, a first run with no working sessions would read every
    account as an error, have nothing to carry forward, and write (then push)
    zeros over the real hand-tracked totals already on the site.
    """
    if LAST_RUN.exists():
        try:
            return json.loads(LAST_RUN.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    if not DJS_TS.exists():
        return {}

    current = DJS_TS.read_text(encoding="utf-8")
    adjustments = {e["id"]: e["manual_adjustment"] for e in config["roster"]}
    seeded = {}
    for dj_id, amount in re.findall(r'id:\s*"([^"]+)".*?amountRaised:\s*(\d+)', current):
        base = max(int(amount) - adjustments.get(dj_id, 0), 0)
        seeded[dj_id] = {"scraped": base, "status": "seeded"}

    total_match = re.search(r"totalRaised:\s*(\d+)", current)
    if total_match:
        seeded["_campaign_total"] = int(total_match.group(1))
    return seeded


def hold_lock():
    """Refuse to run twice at once.

    Two runs would drive the same Playwright profile directories simultaneously,
    and Chromium locks its user-data-dir - the likely collision is the scheduled
    task overlapping a manual run.
    """
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        age = time.time() - LOCK.stat().st_mtime
        if age < 3_600:
            return None
        LOCK.unlink()  # stale lock from a killed run
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return LOCK


def collect(argv, config, prior):
    """Read every account, falling back to the last good scrape total on failure.

    A failed read must never render as $0 - that's the one guarantee this tool
    makes. It's the scraped total (pre-adjustment) that gets carried forward, so
    a later change to manual_adjustment in accounts.json still takes effect even
    while an account's scrape is broken.
    """
    slug = config["campaign_slug"]
    roster = config["roster"]
    wanted = [r for r in roster if r["gofundme_id"] in argv] if argv else roster

    results = {}
    for entry in roster:
        gid = entry["gofundme_id"]
        if not gid:
            results[entry["id"]] = {"scraped": 0, "status": "no-account"}
            continue
        if entry not in wanted:
            was = prior.get(entry["id"])
            results[entry["id"]] = was or {"scraped": 0, "status": "not-read-yet"}
            continue

        label = f"{gid} {entry['fullName']}"
        try:
            scraped = read_account(gid, slug)
            results[entry["id"]] = {"scraped": round(scraped), "status": "ok"}
            print(f"  ok    {label:28} ${scraped:,.0f}")
        except Exception as exc:
            was = prior.get(entry["id"])
            if was:
                results[entry["id"]] = {**was, "status": "stale", "note": str(exc)}
                print(f"  stale {label:28} {exc}  (keeping ${was['scraped']:,})")
            else:
                results[entry["id"]] = {"scraped": 0, "status": "error", "note": str(exc)}
                print(f"  ERROR {label:28} {exc}")

    return results


def render_djs_ts(config, results, total_raised):
    """Rewrite src/data/djs.ts, preserving goalAmount/donateUrl as a human left them."""
    current = DJS_TS.read_text(encoding="utf-8") if DJS_TS.exists() else ""
    goal_match = re.search(r"goalAmount:\s*(\d+)", current)
    donate_match = re.search(r'donateUrl:\s*"([^"]*)"', current)
    goal_amount = int(goal_match.group(1)) if goal_match else 30_000
    donate_url = donate_match.group(1) if donate_match else "https://www.lightsonthelawn.org/dj-competition"

    lines = []
    for entry in config["roster"]:
        r = results[entry["id"]]
        amount = r["scraped"] + entry["manual_adjustment"]
        if entry.get("manual_adjustment_note"):
            lines.append(f"  // {entry['manual_adjustment_note']}")
        lines.append(
            "  { id: %s, djName: %s, fullName: %s, school: %s, amountRaised: %d },"
            % (
                json.dumps(entry["id"]),
                json.dumps(entry["djName"]),
                json.dumps(entry["fullName"]),
                json.dumps(entry["school"]),
                amount,
            )
        )
    dj_lines = "\n".join(lines)

    last_updated = datetime.now().astimezone().isoformat(timespec="seconds")

    return f'''// Real roster + real amounts as of the last nightly update.
// Mick Hooley and Noah Nye Wenner are confirmed at $0 — some donations come
// in through the general campaign rather than a DJ's own link, so the sum
// of amountRaised below will legitimately run behind siteConfig.totalRaised.
//
// Auto-updated nightly by scripts/gofundme-sync/sync.py. Manual adjustments
// (a DJ's own account giving, or general-campaign gifts a scrape can't see)
// live in scripts/gofundme-sync/accounts.json, not here.

export interface DJ {{
  id: string;
  djName: string;
  fullName: string;
  school: string;
  amountRaised: number;
}}

export const djs: DJ[] = [
{dj_lines}
];

export const siteConfig = {{
  goalAmount: {goal_amount},
  // Real overall campaign total — updated nightly alongside the DJ amounts.
  // Includes donations not tied to any DJ's own link, so it may run ahead of
  // the sum of amountRaised across djs[].
  totalRaised: {total_raised},
  // Updated automatically every time sync.py writes this file.
  lastUpdated: {json.dumps(last_updated)},
  donateUrl: {json.dumps(donate_url)},
}};

export function getRankedDJs(): (DJ & {{ rank: number }})[] {{
  return [...djs]
    .sort((a, b) => b.amountRaised - a.amountRaised)
    .map((dj, i) => ({{ ...dj, rank: i + 1 }}));
}}
'''


def write_atomic(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def commit_and_push(no_push):
    status = git("status", "--porcelain", "--", "src/data/djs.ts")
    if not status.stdout.strip():
        print("\n  no change to src/data/djs.ts - nothing to commit")
        return 0

    git("add", "src/data/djs.ts")
    now = datetime.now().astimezone()
    hour12 = now.strftime("%I").lstrip("0") or "12"
    stamp = f'{now.strftime("%Y-%m-%d")} {hour12}:{now.strftime("%M %p")}'
    message = f"Update leaderboard totals for {stamp}"
    result = git("commit", "-m", message)
    if result.returncode != 0:
        print(f"  git commit failed:\n{result.stdout}\n{result.stderr}")
        return 1
    print(f"\n  committed: {message}")

    if no_push:
        print("  --no-push given, leaving it unpushed")
        return 0

    result = git("push")
    if result.returncode != 0:
        print(f"  git push failed:\n{result.stdout}\n{result.stderr}")
        return 1
    print("  pushed")
    return 0


def main(argv):
    dry_run = "--dry-run" in argv
    no_push = "--no-push" in argv or dry_run
    accounts_wanted = [a for a in argv if not a.startswith("-")]

    lock = None if dry_run else hold_lock()
    if lock is None and not dry_run:
        print("another sync is already running - skipping this run")
        return 0

    try:
        config = json.loads((ROOT / "accounts.json").read_text(encoding="utf-8"))
        prior = previous(config)

        results = collect(accounts_wanted, config, prior)

        try:
            total_raised = campaign_snapshot(config["campaign_slug"])
            print(f"\n  campaign  ${total_raised:,}")
        except Exception as exc:
            total_raised = prior.get("_campaign_total", 0)
            print(f"\n  campaign  could not read public page: {exc}  (keeping ${total_raised:,})")

        rendered = render_djs_ts(config, results, total_raised)

        if dry_run:
            print("\n--dry-run: not writing djs.ts or touching git\n")
            print(rendered)
            return 0

        write_atomic(DJS_TS, rendered)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        write_atomic(LAST_RUN, json.dumps({**results, "_campaign_total": total_raised}, indent=2))

        print(f"\n  wrote {DJS_TS.relative_to(REPO)}")
        return commit_and_push(no_push)
    finally:
        if lock:
            lock.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
