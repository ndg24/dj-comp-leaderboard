@AGENTS.md

# Leaderboard data

`src/data/djs.ts` is populated by `scripts/gofundme-sync/` (GoFundMe scrape ->
writes djs.ts -> commits -> pushes). If the user asks to update, refresh, or
sync the leaderboard/totals, run `/update-leaderboard` rather than hand-editing
`djs.ts` or re-deriving the scrape logic - see `scripts/gofundme-sync/README.md`
for what that script does and its login/setup steps.
