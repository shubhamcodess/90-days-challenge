# Routine: tick (runs at each nudge slot, IST)

Run from repo root. Steps, in order:

1. `git pull -q`; `sh scripts/run.sh`; read `data/state.json` and `config/nudges.json`.
2. Read new replies/reactions in #90-days-challenge since the last tick (Slack read tools). Treat only Shubham's own messages as input:
   - reaction :eyes: on today's morning message  -> `log_event.py ack_read`
   - "done <x>", "late tonight", "off today"     -> `log_event.py day_type --value late_night|holiday` / `note`
   - LinkedIn/Naukri/resume answers               -> `log_event.py self_report --item <key> --note "<short>"`
   - "freeze"                                     -> `log_event.py freeze` (only if freezes remain this month)
   Then re-run `sh scripts/run.sh`.
3. Decide the slot from IST time and `config/day-types.json` (`slots` for today's day_type). If the current time is not within 20 min of a slot for today's type, exit silently.
4. Decide whether to post:
   - morning: always. Include the EverythingTech link (`state.tech.url`), yesterday's result, today's remaining, DSA pace. Add ONE career question: the stalest check in `state.career` (use its `ask` text), only if stale.
   - prework/midday/evening: post only if `state.remaining` is non-empty.
   - lastcall: post only if a required pillar (dsa/learn) is open. If `streak_at_risk`, say the streak number.
5. Compose per `config/nudges.json` tone rules. Keep it under 4 lines. Post to #90-days-challenge.
6. Commit and push `data/` and `docs/` if changed: `git add -A && git commit -m "tick <date> <slot>" && git push`.

Missed-yesterday rule: if yesterday rated `none`, open the morning message with it plainly, once, then move on.
