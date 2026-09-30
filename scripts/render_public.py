#!/usr/bin/env python3
"""Allowlist export: state.json -> docs/public.json. New fields stay private unless added here."""
from lib import *
s = read_json(ROOT / "data/state.json"); C = cfg("challenge.json")
show_tk = C["public"]["show_takeaways"]
pub = {
    "generated": s["generated"], "name": C["name"], "start": C["start"], "total_days": s["total_days"],
    "day_number": s["day_number"], "started": s["started"], "finished": s["finished"],
    "streak": s["streak"], "best_streak": s["best_streak"], "streak_at_risk": s["streak_at_risk"],
    "level": s["level"], "xp": s["xp"], "badges": s["badges"],
    "today": {"type": s["day_type"], "done": s["today_done"], "targets": s["today_targets"]},
    "dsa": {k: s["pace"][k] for k in ("goal", "solved", "ideal_by_today", "ahead_by", "needed_per_day")} | {"difficulty": s["difficulty"]},
    "metrics": {k: s["metrics"][k] for k in ("learn_total", "gold_days")},
    "days": [{"day": d["day"], "date": d["date"], "rating": d["rating"], "type": d["type"]} for d in s["days"]],
    "learning": [{"date": x["date"], "topic": x["topic"], "tag": x.get("tag")} | ({"takeaway": x.get("takeaway")} if show_tk else {})
                 for x in s["recent_learning"][:15]],
}
write_json(ROOT / "docs/public.json", pub)
print("public.json written:", len(json.dumps(pub)), "bytes")
