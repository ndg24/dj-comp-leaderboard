# GoFundMe sync for the DJ leaderboard

Pulls each DJ's attributed donation total for the `lotl15` campaign and writes
`src/data/djs.ts`, then commits and pushes so the live site picks it up.

This intentionally does **not** read the "My Impact" tab's headline number -
that figure is lifetime impact across every fundraiser an account has ever
touched, including the account's own personal giving, and drifts from the
real per-campaign total. Instead it calls GoFundMe's own GraphQL query scoped
to the `lotl15` campaign slug, the same approach already proven out in the
sibling `djcompleaderboard` project.

**Note on that sibling project:** its `profiles/` folder (live GoFundMe login
sessions for all 13 accounts) is tracked in git and has been pushed to
GitHub. This setup avoids repeating that - `profiles/`, `credentials.json`,
and `data/` are gitignored here from the start (see `../../.gitignore`). That
older exposure hasn't been touched; it's flagged here as a reminder to deal
with separately, not fixed by this change.

## Setup (once)

```
cd scripts\gofundme-sync
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install chromium
```

## Log the accounts in (once)

```
.venv\Scripts\python login.py --setup
```

Nothing is echoed as you type, nothing is committed to git - `credentials.json`
is gitignored. If a single account has its own password, answer "y" when
asked and enter it for that one, or press Enter to reuse the shared password
for everyone else.

Each account gets its own folder under `profiles/`, created fresh by
Playwright - this never touches your real Chrome profile.

```
.venv\Scripts\python login.py            # signs everything in, unattended
.venv\Scripts\python login.py dj07 --show   # debug one account, visible window
```

Re-run `login.py` (no args) any time a session expires - accounts that
already work are skipped.

## Run it by hand

```
.venv\Scripts\python sync.py             # all accounts, then commit + push
.venv\Scripts\python sync.py dj01        # just one account, for debugging
.venv\Scripts\python sync.py --dry-run   # print what would change, touch nothing
.venv\Scripts\python sync.py --no-push   # write + commit but don't push
```

Or just run `run-sync.bat` from a terminal (open one first - don't
double-click it, or the window closes before you can read the output).

A failed read never renders as $0 - it carries the last good total forward
instead. That guarantee also covers the very first run, before any account
has ever been read: it seeds from whatever amounts are already committed in
`src/data/djs.ts`.

## Adjustments a scrape structurally can't see

Some DJs' totals include money that never shows up in this scrape - a
donation made through their own personal GoFundMe account instead of their
campaign link, or a gift that went straight to the charity's general pool
instead of any DJ's own link. Add that as `manual_adjustment` (and an
optional `manual_adjustment_note`, rendered as a comment above their line in
`djs.ts`) in `accounts.json`, rather than hand-editing amounts. Right now
that's just Hunter Truitt, at +$355.

DJs with no GoFundMe account at all (`gofundme_id: null` in `accounts.json` -
currently Mick Hooley and Noah Nye Wenner) always resolve to their
`manual_adjustment` alone, so a direct-to-charity donation for either of them
is entered the same way.

## Every day at 6pm, with manual runs too

```
schtasks /create /tn "LOTL Leaderboard Sync" /xml task.xml
```

`task.xml` sets `StartWhenAvailable`, so a run missed because the laptop was
asleep or off at 6pm fires as soon as it's next on - same idea as launchd's
wake-and-run behavior on the Mac version. It runs under your logged-on
session (not "whether logged on or not"), since a closed laptop can't run
anything regardless.

To run it right now, on demand:

```
schtasks /run /tn "LOTL Leaderboard Sync"
```

or just run `run-sync.bat` / `.venv\Scripts\python sync.py` directly.

Check on it, or remove it:

```
schtasks /query /tn "LOTL Leaderboard Sync" /v /fo list
schtasks /delete /tn "LOTL Leaderboard Sync" /f
```

Output from every run, scheduled or manual, appends to `data\run.log`.
