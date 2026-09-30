---
name: learn
description: Log a learning/research session to the 90-day challenge ledger. Use when the user says /learn or "log this", or when a tech / DSA / system-design / company-prep research or study session with Claude wraps up.
---

# /learn

Repo: `~/Development/90-days-challenge` (always work there, from any directory).

1. Infer, don't interrogate: `topic` (short), `tag` (dsa, system-design, lld, company-prep, behavioral, tech, career), `takeaway` (1-2 sentences: what Shubham now knows), optional `minutes`.
2. Run:
   `cd ~/Development/90-days-challenge && git pull -q --rebase && python3 scripts/log_event.py learn --topic "..." --tag <tag> --takeaway "..." [--minutes N] && sh scripts/run.sh`
3. Commit and push: `git add -A && git commit -q -m "learn: <topic>" && git push -q`
4. Reply with one line: today's remaining quests (from `data/state.json` `remaining`).

The repo is public: no company names, offers, salaries or personal details in topic/takeaway.
