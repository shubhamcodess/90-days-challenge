# 90 Days Challenge

Claude-run accountability for a 90-day interview-prep push (Oct 1 to Dec 29, 2026).
Ledger of events -> derived state -> Slack nudges + pixel status page. Reads `lets-dsa-sp`, `career-os-sp`, `everything-tech-newsletter`.

```
sh scripts/run.sh                     # collect -> score -> export
python3 scripts/log_event.py learn --topic "..." --tag dsa --takeaway "..."
python3 -m http.server --directory docs   # preview the page
```
Extend: add `config/pillars/<id>.json`, edit `config/day-types.json` / `badges.json`, or drop a plain-English rule in `inbox.md`.
See `CLAUDE.md` and `routines/`.
