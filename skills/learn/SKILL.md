---
name: learn
description: Log a learning/research session to the 90-day challenge ledger. Use when the user says /learn or "log this", or when a tech / company-prep / interview-prep research or study session with Claude wraps up.
---

# /learn

1. Ask for nothing you can infer. Derive: `topic` (short), `tag` (dsa, system-design, lld, company-prep, behavioral, tech, career), `takeaway` (1-2 sentences, what Shubham now knows), optional `minutes`.
2. From the 90-days-challenge repo root run:
   `python3 scripts/log_event.py learn --topic "..." --tag <tag> --takeaway "..." [--minutes N]`
3. `sh scripts/run.sh`, commit (`learn: <topic>`) and push. Reply with one line: today's remaining quests.
Never include company names, offers or personal details in topic/takeaway; this repo is public.
