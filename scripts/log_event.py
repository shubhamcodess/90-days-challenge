#!/usr/bin/env python3
"""Append an event to the ledger.
  log_event.py learn --topic "Consistent hashing" --tag system-design --takeaway "..." [--minutes 30]
  log_event.py ack_read [--date YYYY-MM-DD]
  log_event.py self_report --item linkedin --note "posted about X"
  log_event.py day_type --value late_night [--date ...]
  log_event.py freeze [--date ...]
  log_event.py note --text "..."
"""
import argparse
from lib import *

ap = argparse.ArgumentParser()
ap.add_argument("type", choices=["learn", "ack_read", "self_report", "day_type", "freeze", "note"])
ap.add_argument("--date"); ap.add_argument("--topic"); ap.add_argument("--tag")
ap.add_argument("--takeaway"); ap.add_argument("--minutes", type=int)
ap.add_argument("--item"); ap.add_argument("--note"); ap.add_argument("--value"); ap.add_argument("--text")
a = ap.parse_args()
data = {k: v for k, v in dict(topic=a.topic, tag=a.tag, takeaway=a.takeaway, minutes=a.minutes,
                              item=a.item, note=a.note, value=a.value, text=a.text).items() if v is not None}
if a.type == "learn":
    assert a.topic and a.takeaway, "learn needs --topic and --takeaway"
    tags = pillar("learn")["tags"]
    if a.tag and a.tag not in tags:
        raise SystemExit(f"tag must be one of {tags}")
if a.type == "self_report":
    keys = [c["key"] for c in pillar("career")["checks"]]
    assert a.item in keys, f"--item must be one of {keys}"
print(json.dumps(append_event(a.type, data, a.date), ensure_ascii=False))
