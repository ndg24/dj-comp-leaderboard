#!/usr/bin/env python3
"""Log every DJ's GoFundMe account in, unattended.

Reads credentials from credentials.json (gitignored, never committed) and signs
each account into its own isolated Playwright profile under profiles/. sync.py
lives off the saved sessions afterwards. Re-run any time a session expires -
accounts that already work are skipped.

    py login.py --setup            # enter the passwords (nothing echoed)
    py login.py --setup dj08 dj09  # re-enter just these, leaving the rest alone
    py login.py           # log in everything that isn't already working
    py login.py dj01      # just this one
    py login.py --show    # visible windows, for when something breaks
    py login.py --force   # re-login even accounts that currently work

GoFundMe's sign-in is two-step: email, Continue, then password.
"""

import getpass
import json
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / "profiles"
CREDS = ROOT / "credentials.json"

SIGNIN_URL = "https://www.gofundme.com/sign-in"
IMPACT_URL = "https://www.gofundme.com/account/impact"


def accounts():
    roster = json.loads((ROOT / "accounts.json").read_text(encoding="utf-8"))["roster"]
    return [a for a in roster if a.get("gofundme_id")]


def setup(only=None):
    """Ask for the passwords rather than making someone hand-edit JSON.

    Pass account ids to re-enter just those, leaving every other saved password
    alone - useful when a handful were mistyped.
    """
    existing = json.loads(CREDS.read_text(encoding="utf-8")) if CREDS.exists() else {}
    shared = existing.get("default_password", "")
    overrides = dict(existing.get("overrides") or {})

    print("\nNothing is echoed as you type. Nothing is committed to git.\n")

    if only:
        targets = [a for a in accounts() if a["gofundme_id"] in only]
        if not targets:
            print(f"no such account ids: {', '.join(only)}")
            return 1
        print("Enter each password. Press Enter alone to leave one unchanged.\n")
    else:
        shared = getpass.getpass("Password most accounts share: ").strip()
        if not shared:
            print("nothing entered, aborting.")
            return 1
        answer = input("\nDo some accounts have a different password? [y/N] ").strip().lower()
        if not answer.startswith("y"):
            targets = []
        else:
            targets = accounts()
            print("\nEnter a password, or press Enter to use the shared one.\n")

    for account in targets:
        gid = account["gofundme_id"]
        entry = getpass.getpass(f"  {gid}  {account['email']}: ").strip()
        if entry:
            overrides[gid] = entry
        elif not only:
            overrides.pop(gid, None)

    CREDS.write_text(json.dumps({
        "_comment": "Gitignored. Written by login.py --setup.",
        "default_password": shared,
        "overrides": overrides,
    }, indent=2), encoding="utf-8")
    CREDS.chmod(0o600)

    print(f"\nSaved. {len(overrides)} account(s) with their own password.")
    return 0


def credentials():
    if not CREDS.exists():
        sys.exit(f"no {CREDS.name} - run: py login.py --setup")
    data = json.loads(CREDS.read_text(encoding="utf-8"))
    default = data.get("default_password") or ""
    overrides = data.get("overrides") or {}
    resolved = {}
    for account in accounts():
        gid = account["gofundme_id"]
        pw = overrides.get(gid) or default
        if pw:
            resolved[gid] = pw
    return resolved


def logged_in(page):
    """Confirm we landed on the impact page itself.

    Signed out, GoFundMe bounces to /sign-up (not /sign-in), so checking for the
    destination is the only reliable test - blacklisting redirect URLs silently
    reports success for a profile that was never logged in.
    """
    page.goto(IMPACT_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(2_500)
    return page.url.startswith(IMPACT_URL)


def sign_in(page, email, password):
    """Two-step Descope form: email, Enter, password, Enter.

    The fields are Vaadin web components with no plain <button>, so submit
    with Enter. As of 2026-09-19 the email field is a <vaadin-email-field>
    wrapping an <input type="text" name="email">, not type="email" - matching
    on type alone finds nothing. An async consent-banner widget
    (#transcend-consent-manager) sometimes overlaps the field for a moment
    after load; force=True on fill() skips Playwright's actionability/overlap
    check rather than us hunting for that banner's transient content.
    """
    page.goto(SIGNIN_URL, wait_until="domcontentloaded", timeout=45_000)

    email_box = page.locator('input[name="email"]')
    email_box.wait_for(state="visible", timeout=30_000)
    email_box.fill(email, force=True)
    email_box.press("Enter")

    # The password field isn't in the DOM until after email submission, so
    # unlike email this couldn't be confirmed ahead of time - type="password"
    # is kept as well as name="password" since masking makes type="password"
    # far more likely to have survived here than it did on the email field.
    password_box = page.locator('input[type="password"], input[name="password"]')
    password_box.wait_for(state="visible", timeout=30_000)
    password_box.fill(password, force=True)
    password_box.press("Enter")

    page.wait_for_timeout(6_000)
    return form_error(page)


def form_error(page):
    """Whatever the form is complaining about, so a failure says why not just where.

    The Descope form renders inside shadow DOM, so inner_text('body') comes back
    empty - the roots have to be walked explicitly.
    """
    try:
        leaves = page.evaluate("""() => {
          const out = [];
          const walk = root => {
            for (const el of root.querySelectorAll('*')) {
              if (el.shadowRoot) walk(el.shadowRoot);
              const t = (el.textContent || '').trim();
              if (t && t.length < 140 && el.children.length === 0) out.push(t);
            }
          };
          walk(document);
          return [...new Set(out)];
        }""")
    except Exception:
        return None

    for line in leaves:
        lowered = line.lower()
        if any(word in lowered for word in
               ("check your email and password", "incorrect", "invalid", "locked",
                "too many", "does not match", "couldn't", "could not", "expired")):
            return line
    return None


def run(account, password, show, force):
    gid = account["gofundme_id"]
    profile = PROFILES / gid
    profile.mkdir(parents=True, exist_ok=True)
    label = f"{gid} {account['fullName']}"

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(profile), headless=not show, viewport={"width": 1280, "height": 900}
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            if not force and logged_in(page):
                print(f"  skip  {label:28} already signed in")
                return True

            complaint = sign_in(page, account["email"], password)

            if logged_in(page):
                print(f"  ok    {label:28} signed in")
                return True

            reason = complaint or f"still on {page.url.split('?')[0]}"
            print(f"  FAIL  {label:28} {reason}")
            return False
        except PWTimeout as exc:
            print(f"  FAIL  {label:28} timed out ({str(exc).splitlines()[0][:60]})")
            return False
        except Exception as exc:
            print(f"  FAIL  {label:28} {exc}")
            return False
        finally:
            ctx.close()


def main(argv):
    if "--setup" in argv:
        return setup([a for a in argv if not a.startswith("-")] or None)

    show = "--show" in argv
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("-")]

    todo = accounts()
    if wanted:
        todo = [a for a in todo if a["gofundme_id"] in wanted]

    creds = credentials()
    missing = [a["gofundme_id"] for a in todo if a["gofundme_id"] not in creds]
    if missing:
        print(f"no password for: {', '.join(missing)} - check {CREDS.name}")
        todo = [a for a in todo if a["gofundme_id"] in creds]
    if not todo:
        return 1

    failed = [a["gofundme_id"] for a in todo if not run(a, creds[a["gofundme_id"]], show, force)]

    print(f"\n{len(todo) - len(failed)}/{len(todo)} signed in.")
    if failed:
        print(f"failed: {', '.join(failed)}")
        print("Re-run those with --show to watch what happens.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
