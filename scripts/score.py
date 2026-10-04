#!/usr/bin/env python3
"""Derive data/state.json from ledger + collected.json. Pure function of those inputs."""
import math, re
from collections import defaultdict
from lib import *

C = cfg("challenge.json"); DT = cfg("day-types.json"); HOL = cfg("holidays.json")["dates"]
BADGES = cfg("badges.json"); CAREER = pillar("career")
START = parse_date(C["start"]); END = START + dt.timedelta(days=C["days"] - 1)
DEADLINE = parse_date(C["goal_deadline"])
WD = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

def day_type(d, overrides):
    if d.isoformat() in overrides: return overrides[d.isoformat()]
    if d.isoformat() in HOL: return "holiday"
    return DT["default_by_weekday"][WD[d.weekday()]]

def main():
    ev = ledger_events(); col = read_json(ROOT / "data/derived/collected.json", {})
    overrides = {e["date"]: e["data"]["value"] for e in ev if e["type"] == "day_type"}
    freezes = {e["date"] for e in ev if e["type"] == "freeze"}
    amend = {e['data']['target']: e['data'] for e in ev if e['type'] == 'amend'}
    learn = defaultdict(list); acks = set()
    for e in ev:
        if e["type"] == "learn":
            fix = {k: v for k, v in amend.get(e["ts"], {}).items() if k in ("topic", "takeaway", "tag")}
            learn[e["date"]].append(e["data"] | fix | {"date": e["date"]})
        if e["type"] == "ack_read": acks.add(e["data"].get("date", e["date"]))
    solved = defaultdict(list); baseline = 0
    for s in col.get("dsa", {}).get("solved", []):
        if s["solved_on"] >= C["start"]: solved[s["solved_on"]].append(s)
        else: baseline += 1
    t = today(); last = min(t, END); days = []; run = best = 0; used_freezes = defaultdict(int)
    d = START
    while d <= last:
        k = d.isoformat(); typ = day_type(d, overrides)
        tg = DT["types"][typ]["targets"]
        done = {"dsa": len(solved[k]), "learn": len(learn[k]), "tech": 1 if k in acks else 0}
        req_ok = all(done[p] >= 1 for p in C["streak_requires"])
        frozen = k in freezes and not req_ok
        if frozen and used_freezes[k[:7]] >= C["freezes_per_month"]: frozen = False
        if frozen: used_freezes[k[:7]] += 1
        rating = "none"
        if req_ok:
            rating = "bronze"
            if done["tech"]: rating = "silver"
            if done["tech"] and done["dsa"] >= 2: rating = "gold"
        elif frozen: rating = "frozen"
        kept = req_ok or frozen
        if d < t:
            run = run + 1 if kept else 0
        elif kept:  # today counts once done; if not done yet, streak is "at risk", not broken
            run += 1
        best = max(best, run)
        days.append({"date": k, "day": (d - START).days + 1, "type": typ, "done": done, "targets": tg, "rating": rating})
        d += dt.timedelta(days=1)
    today_row = next((x for x in days if x["date"] == t.isoformat()), None)
    streak = run if (today_row is None or today_row["rating"] not in ("none",)) else run
    if today_row and today_row["rating"] == "none":
        streak = run  # run was not incremented today, so it equals yesterday's streak
    dsa_total = sum(len(v) for v in solved.values())
    diff = defaultdict(int)
    for v in solved.values():
        for s in v: diff[s.get("difficulty") or "?"] += 1
    goal = pillar("dsa")["goal_total"]
    elapsed = (min(t, DEADLINE) - START).days + 1; span = (DEADLINE - START).days + 1
    ideal = goal * elapsed / span; days_left = max((DEADLINE - t).days + 1, 1)
    pace = {"goal": goal, "solved": dsa_total, "ideal_by_today": round(ideal, 1),
            "ahead_by": round(dsa_total - ideal, 1), "needed_per_day": round(max(goal - dsa_total, 0) / days_left, 2),
            "days_left_to_deadline": days_left, "baseline_before_start": baseline}
    # career freshness
    checks = []
    for c in CAREER["checks"]:
        last_d = (col.get("career", {}) or {}).get(c["key"]) if c.get("auto") else None
        for e in ev:
            if e["type"] == "self_report" and e["data"].get("item") == c["key"]:
                last_d = max(last_d, e["date"]) if last_d else e["date"]
        age = (t - parse_date(last_d)).days if last_d else None
        checks.append({"key": c["key"], "label": c["label"], "last": last_d, "age_days": age,
                       "fresh": age is not None and age <= c["max_age_days"], "ask": c["ask"], "max_age_days": c["max_age_days"]})
    # today
    typ_today = day_type(t, overrides); tg = DT["types"][typ_today]["targets"]
    dn = today_row["done"] if today_row else {"dsa": 0, "learn": 0, "tech": 0}
    remaining = []
    for p in ("dsa", "learn"):
        if dn[p] < tg[p]: remaining.append({"pillar": p, "need": tg[p] - dn[p]})
    if not dn["tech"]: remaining.append({"pillar": "tech", "need": 1})
    metrics = {"dsa_total": dsa_total, "best_streak": best, "hard_total": diff.get("Hard", 0),
               "learn_total": sum(len(v) for v in learn.values()), "gold_days": sum(1 for x in days if x["rating"] == "gold"),
               "career_fresh": sum(1 for c in checks if c["fresh"])}
    badges = []
    for b in BADGES:
        m = re.match(r"(\w+)>=(\d+)", b["rule"])
        if m and metrics.get(m[1], 0) >= int(m[2]): badges.append(b["id"])
    xp = sum({"bronze": 5, "silver": 6, "gold": 8}.get(x["rating"], 0) for x in days) * C["xp"]["per_point"] \
         + dsa_total * 20 + metrics["learn_total"] * 10
    state = {"generated": now().isoformat(timespec="seconds"), "today": t.isoformat(), "day_number": (t - START).days + 1,
             "total_days": C["days"], "started": t >= START, "finished": t > END,
             "day_type": typ_today, "streak": streak, "best_streak": best, "streak_at_risk": bool(today_row) and today_row["rating"] == "none" and streak > 0,
             "today_done": dn, "today_targets": tg, "remaining": remaining, "pace": pace, "metrics": metrics,
             "badges": badges, "xp": xp, "level": xp // C["xp"]["level_every"] + 1, "career": checks,
             "tech": col.get("tech", {}), "sources": {k: ("error" if isinstance(v, dict) and "error" in v else "ok") for k, v in col.items() if isinstance(v, dict)}, "days": days, "difficulty": dict(diff),
             "solved_log": sorted([{"date": k, "title": x.get("title"), "difficulty": x.get("difficulty"), "pattern": x.get("pattern")} for k, v in solved.items() for x in v], key=lambda x: (x["date"], x["title"] or "")),
             "recent_learning": sorted([x for v in learn.values() for x in v], key=lambda x: x["date"], reverse=True)[:80]}
    write_json(ROOT / "data/state.json", state)
    print(f"Day {state['day_number']}/{C['days']} | {typ_today} | streak {streak} (best {best}) | DSA {dsa_total}/{goal} ({pace['ahead_by']:+}) | done {dn} | remaining {[r['pillar'] for r in remaining]}")

if __name__ == "__main__": main()
