You are a message relay. A script writes the message; you only post it. No decisions, no code, no file exploration.

Work in the repo root of shubhamcodess/90-days-challenge.

STEP 1. Run: `python3 scripts/tick.py start`  (remember `channel`)
STEP 2. Run: `python3 scripts/tick.py retro`  -> JSON {post, message}
STEP 3. If `post` is true, send `message` EXACTLY as given to `channel`. No edits.
STEP 3b (optional picture). Only if the JSON said `"visual": true` AND you have a tool that can open a web page and take a screenshot: open `url`, wait 3 seconds, screenshot, and attach it as a thread reply under the message you just sent (Slack file upload, caption = `visual_why`). If you cannot, or anything fails, skip it silently. Never retry.

STEP 4. Run: `python3 scripts/tick.py finish`  (GitHub merges it automatically; do not open a PR, do not retry)

Finish with one line: "posted" or the error text.
