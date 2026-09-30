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

# ---- README banner: docs/progress.svg (auto-updated with every run) ----
def banner(p):
    col = {"gold": "#7cc0bb", "silver": "#519294", "bronze": "#3b6a6d", "none": "#4a3a5c", "frozen": "#3d4b7c", "": "#262a52"}
    byday = {d["day"]: d for d in p["days"]}
    n, W = p["total_days"], 600
    cw = (W - 40) / n
    day = "".join(f'<rect x="{20 + i * cw:.2f}" y="56" width="{cw - 1.2:.2f}" height="16" fill="{col.get(byday.get(i + 1, {}).get("rating", ""), col[""])}"/>' for i in range(n))
    g, sv = p["dsa"]["goal"], p["dsa"]["solved"]
    gw = (W - 40) / g
    dsa = "".join(f'<rect x="{20 + i * gw:.2f}" y="110" width="{gw - 1.2:.2f}" height="16" fill="{"#7cc0bb" if i < sv else "#262a52"}"/>' for i in range(g))
    pm = 20 + p["dsa"]["ideal_by_today"] * gw
    d = min(p["day_number"], n) if p["started"] else 0
    t = lambda x, y, s, fill="#e9e7ff", size=13, anchor="start": f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}" font-family="ui-monospace,Menlo,Consolas,monospace" font-weight="bold">{s}</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="176" viewBox="0 0 {W} 176" shape-rendering="crispEdges">'
            f'<rect width="{W}" height="176" fill="#1b1838"/><rect x="2" y="2" width="{W - 4}" height="172" fill="none" stroke="#322f60" stroke-width="2"/>'
            + t(20, 34, f"DAY {d}/{n}") + t(W - 20, 34, f"STREAK {p['streak']}  BEST {p['best_streak']}  LVL {p['level']}", "#9a9cc4", 12, "end")
            + day + t(20, 98, f"SOLVED {sv}/{g}") + t(W - 20, 98, f"{p['dsa']['ahead_by']:+} vs plan", "#9a9cc4", 12, "end")
            + dsa + (f'<rect x="{pm - 1:.1f}" y="106" width="2" height="24" fill="#e9e7ff"/>' if p["started"] else "")
            + t(20, 156, f"updated {p['generated'][:10]}", "#6f719c", 11) + '</svg>')

(ROOT / "docs/progress.svg").write_text(banner(pub))
