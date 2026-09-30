# Routine: weekly retro (Sunday ~20:00 IST)

1. `git pull -q; sh scripts/run.sh`; read `data/state.json`, the week's ledger, `inbox.md`.
2. Post to Slack (max 8 lines): week scorecard (days by rating), DSA solved vs pace, patterns touched, learning topics count, stale career checks, one thing to change next week.
3. Fold any rules in `inbox.md` into `config/` (small, reviewable edits), then clear the handled lines from `inbox.md`. Say what changed.
4. Recompute needed DSA/day; if >1.5, propose an explicit weekend catch-up plan.
5. Commit and push.
