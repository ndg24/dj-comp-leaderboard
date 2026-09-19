---
description: Scrape all 15 GoFundMe accounts and push updated leaderboard totals
---

Run `scripts/gofundme-sync/sync.py` right now to refresh the DJ leaderboard:

1. From the repo root, run: `scripts\gofundme-sync\.venv\Scripts\python.exe scripts\gofundme-sync\sync.py`
2. That script itself writes `src/data/djs.ts`, commits, and pushes to `main` -
   do not run any git commands yourself around it, it already handles that.
3. Report back concisely: each DJ's new total vs what changed, the campaign
   total, and whether it committed/pushed (or why not - e.g. "no change" is a
   normal, successful outcome, not an error).

If any account comes back "stale" or "error" in the output, say which one(s)
and why (from the printed note), but don't try to fix the login yourself -
that needs `login.py`, run interactively by the user with their password.

If `.venv` doesn't exist at that path, or accounts have never been logged in,
stop and point the user at `scripts/gofundme-sync/README.md` rather than
trying to set any of that up in the middle of this command.
