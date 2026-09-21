#!/usr/bin/env python3
"""Poll the public GoFundMe campaign total; run the full sync when it moves.

For a window where donations might land in bursts (e.g. a live event), this
gives faster-than-5-hourly updates without hammering the per-account scrape -
each poll is one unauthenticated request to the public campaign page
(sync.campaign_snapshot), the same call sync.py itself uses for the headline
total. Only when that number changes does it shell out to the full sync.py,
which re-scrapes every account, writes djs.ts, commits, and pushes.

    py watch.py                  # poll every 60s for 120 minutes
    py watch.py --interval 90    # custom poll interval, seconds
    py watch.py --minutes 150    # custom watch duration, minutes
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from time import sleep

import sync  # sibling module - campaign_snapshot(), ROOT, LAST_RUN


def log(msg):
    print(f"{datetime.now().isoformat(timespec='seconds')}  {msg}", flush=True)


def last_known_total(slug):
    if sync.LAST_RUN.exists():
        try:
            data = json.loads(sync.LAST_RUN.read_text(encoding="utf-8"))
            if "_campaign_total" in data:
                return data["_campaign_total"]
        except json.JSONDecodeError:
            pass
    return sync.campaign_snapshot(slug)


def run_full_sync():
    result = subprocess.run(
        [sys.executable, str(sync.ROOT / "sync.py")],
        cwd=sync.ROOT, capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        log(f"  sync| {line}")
    if result.returncode != 0:
        log(f"  sync.py exited {result.returncode}:\n{result.stderr}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60, help="seconds between checks")
    parser.add_argument("--minutes", type=int, default=120, help="how long to keep watching")
    args = parser.parse_args()

    config = json.loads((sync.ROOT / "accounts.json").read_text(encoding="utf-8"))
    slug = config["campaign_slug"]

    last_total = last_known_total(slug)
    log(f"watching '{slug}' every {args.interval}s for {args.minutes}m - starting total ${last_total:,}")

    deadline = datetime.now() + timedelta(minutes=args.minutes)
    while datetime.now() < deadline:
        sleep(args.interval)
        try:
            total = sync.campaign_snapshot(slug)
        except Exception as exc:
            log(f"check failed: {exc}")
            continue

        if total != last_total:
            log(f"total changed ${last_total:,} -> ${total:,} - running full sync")
            run_full_sync()
            last_total = total
        else:
            log(f"no change (${total:,})")

    log("watch window ended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
