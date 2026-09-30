#!/usr/bin/env python3
"""Allowlist export: state.json -> docs/public.json. New fields stay private unless added here."""
import re
from lib import *
s = read_json(ROOT / "data/state.json"); C = cfg("challenge.json")
show_tk = C["public"]["show_takeaways"]
PRIVATE_METRICS = {"career_fresh"}  # career detail never goes public, even as a counter
badges = []
for b in cfg("badges.json"):
    m = re.match(r"(\w+)>=(\d+)", b["rule"])
    if not m or m[1] in PRIVATE_METRICS:
        if b["id"] in s["badges"]: badges.append({"id": b["id"], "name": b["name"], "desc": b["desc"], "earned": True, "cur": 1, "target": 1})
        continue
    cur = s["metrics"].get(m[1], 0); tgt = int(m[2])
    badges.append({"id": b["id"], "name": b["name"], "desc": b["desc"], "earned": b["id"] in s["badges"], "cur": min(cur, tgt), "target": tgt})
pub = {
    "generated": s["generated"], "name": C["name"], "start": C["start"], "total_days": s["total_days"],
    "day_number": s["day_number"], "started": s["started"], "finished": s["finished"],
    "streak": s["streak"], "best_streak": s["best_streak"], "streak_at_risk": s["streak_at_risk"],
    "level": s["level"], "xp": s["xp"], "level_every": C["xp"]["level_every"], "badges": badges,
    "today": {"type": s["day_type"], "done": s["today_done"], "targets": s["today_targets"]},
    "dsa": {k: s["pace"][k] for k in ("goal", "solved", "ideal_by_today", "ahead_by", "needed_per_day", "days_left_to_deadline")}
           | {"difficulty": s["difficulty"]},
    "metrics": {k: s["metrics"][k] for k in ("learn_total", "gold_days")},
    "days": [{"day": d["day"], "date": d["date"], "rating": d["rating"], "type": d["type"], "done": d["done"]} for d in s["days"]],
    "solved": s["solved_log"],
    "learning": [{"date": x["date"], "topic": x["topic"], "tag": x.get("tag")} | ({"takeaway": x.get("takeaway")} if show_tk else {})
                 for x in s["recent_learning"]],
}
write_json(ROOT / "docs/public.json", pub)
print("public.json written:", len(json.dumps(pub)), "bytes")
