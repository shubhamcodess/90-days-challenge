#!/usr/bin/env python3
"""Deterministic brain for the Slack routine. All judgment lives here, the model only moves text.
  tick.py start                      git pull + refresh; prints {channel, user, morning_ts, last_seen_ts, now}
  tick.py ingest <ts> "<text>"       parse one message from the owner; prints {action, reply}
  tick.py ack                        owner reacted :eyes: on the morning message
  tick.py decide [--slot S] [--force] prints {post, slot, message}
  tick.py posted <slot> <ts>         record a post (ts of the Slack message)
  tick.py retro                      prints {post, message} for the weekly review
  tick.py finish                     refresh, commit, push
"""
import shutil, subprocess, sys
from lib import *

C = cfg("challenge.json"); DT = cfg("day-types.json")
SEEN = ROOT / "data/cache/slack.json"
ALIAS = {"linkedin": "linkedin", "naukri": "naukri", "resume": "resume_tailored", "jobs": "job_research", "exp": "master_experience"}
SLOT_WINDOW_MIN = 25

def sh(*a): return subprocess.run(a, cwd=ROOT, capture_output=True, text=True)
def refresh(): sh("sh", "scripts/run.sh")
def state(): return read_json(ROOT / "data/state.json")
def seen(): return read_json(SEEN, {"last_ts": "0", "morning_ts": {}, "posted": {}})
def out(o): print(json.dumps(o, ensure_ascii=False))

def open_items(s):
    names = {"dsa": "DSA", "learn": "learn entry", "tech": "read"}
    return [f"{r['need']} {names[r['pillar']]}" if r["pillar"] != "tech" else "read" for r in s["remaining"]]

def required_open(s):
    return [r for r in s["remaining"] if r["pillar"] in C["streak_requires"]]

def stalest(s):
    stale = [c for c in s["career"] if not c["fresh"]]
    stale.sort(key=lambda c: -(c["age_days"] if c["age_days"] is not None else 999))
    return stale[0] if stale else None

def head(s): return f"Day {s['day_number']}/{s['total_days']}"

def yesterday(s):
    y = (parse_date(s["today"]) - dt.timedelta(days=1)).isoformat()
    row = next((d for d in s["days"] if d["date"] == y), None)
    if not row: return None
    if row["rating"] in ("none",): return "Yesterday: missed. Streak reset. Today is the restart."
    d = row["done"]
    return f"Yesterday: {row['rating']} (DSA {d['dsa']}, learn {d['learn']}, read {'yes' if d['tech'] else 'no'})"

def compose(slot, s):
    left = ", ".join(open_items(s)) or "nothing"
    st = s["streak"]; p = s["pace"]
    if slot == "morning":
        lines = [f"{head(s)} · streak {st} · {s['day_type'].replace('_', ' ')}"]
        if s["day_number"] == 1: lines.insert(0, "Day 1. 90 days, one problem, one lesson, one read at a time. Begin.")
        y = yesterday(s)
        if y: lines.append(y)
        lines.append(f"Today: DSA {s['today_done']['dsa']}/{s['today_targets']['dsa']} · learn {s['today_done']['learn']}/{s['today_targets']['learn']} · read {s['tech'].get('url', '')} (react 👀)")
        lines.append(f"100-goal: {p['solved']}/{p['goal']} ({p['ahead_by']:+} vs plan, need {p['needed_per_day']}/day)")
        q = stalest(s)
        if q: lines.append("Q: " + q["ask"])
        lines.append(LINES[s["day_number"] % len(LINES)])
        return "\n".join(lines)
    if slot in ("prework", "midday", "evening"):
        if not s["remaining"]: return None
        tail = f" Streak {st} on the line." if st and required_open(s) else ""
        label = {"prework": "before work", "midday": "midday", "evening": "evening"}[slot]
        return f"{head(s)} · {label}\nOpen: {left}.{tail}"
    if slot == "lastcall":
        if not required_open(s): return None
        if st: return f"Last call. Streak {st} ends at midnight.\nOpen: {left}. One problem saves it."
        return f"Last call. Open: {left}. One problem starts the streak."
    return None

def visual_reason(slot, s):
    """Deterministic 'worth a picture' rule: milestones, morning only."""
    if slot != "morning": return None
    v = C["visual"]
    if s["streak"] in v["streaks"]: return f"{s['streak']}-day streak"
    if s["pace"]["solved"] in v["dsa_counts"]: return f"{s['pace']['solved']} problems"
    return None

LINES = ["Small steps, every day. That is the whole trick.", "Consistency beats intensity. Show up.", "You do not need a perfect day, just a done one.",
         "Future you is already grateful for today.", "One problem is a vote for who you are becoming.", "Calm and steady wins.", "Do the next small thing.",
         "Progress is quiet. Keep going.", "Start before you feel ready.", "Momentum is built one day at a time.", "Easy days count too.", "Trust the process, log the work."]

def pick_slot(s, force):
    slots = DT["types"][s["day_type"]]["slots"]; n = now(); best = None
    # catch-up: if the morning post was missed, send it on the next run until the evening window
    mh, mm = map(int, DT["slots"]["morning"]["ist"].split(":")); mins = n.hour * 60 + n.minute
    if "morning" in slots and "morning" not in seen()["posted"].get(today().isoformat(), []) and mh * 60 + mm < mins < 20 * 60 + 30:
        return "morning"
    for name in slots:
        h, m = map(int, DT["slots"][name]["ist"].split(":"))
        diff = abs((n.hour * 60 + n.minute) - (h * 60 + m))
        if diff <= SLOT_WINDOW_MIN and (best is None or diff < best[0]): best = (diff, name)
    return best[1] if best else None

def cmd_start():
    sh("git", "pull", "-q", "--rebase"); refresh(); z = seen()
    out({"channel": C["slack_channel_id"], "user": C["slack_user_id"], "last_seen_ts": z["last_ts"],
         "morning_ts": z["morning_ts"].get(today().isoformat()), "now": now().isoformat(timespec="minutes")})

def cmd_ingest(ts, text):
    z = seen(); t = text.strip(); low = t.lower(); act, reply = "ignored", ""
    if float(ts) > float(z["last_ts"]): z["last_ts"] = ts
    def log(*a): sh("python3", "scripts/log_event.py", *a)
    if low in ("late", "late tonight"):
        log("day_type", "--value", "late_night"); act, reply = "day_type", "Got it: lite bar tonight (DSA 1 + learn 1)."
    elif low in ("off", "holiday", "off today"):
        log("day_type", "--value", "holiday"); act, reply = "day_type", "Got it: holiday mode today."
    elif low == "freeze":
        month = today().isoformat()[:7]
        used = sum(1 for e in ledger_events() if e["type"] == "freeze" and e["date"].startswith(month))
        if used < C["freezes_per_month"]:
            log("freeze"); act, reply = "freeze", "Freeze used for today. None left this month."
        else:
            act, reply = "freeze_denied", "No freezes left this month."
    elif low == "read":
        log("ack_read"); act, reply = "ack_read", "Read logged."
    elif ":" in t and t.split(":", 1)[0].strip().lower() in ALIAS:
        k, note = t.split(":", 1); log("self_report", "--item", ALIAS[k.strip().lower()], "--note", note.strip()[:200])
        act, reply = "self_report", f"Logged: {ALIAS[k.strip().lower()]}."
    elif low.startswith("learn:") and t.count("|") == 2:
        topic, tag, tk = [x.strip() for x in t.split(":", 1)[1].split("|")]
        log("learn", "--topic", topic, "--tag", tag, "--takeaway", tk); act, reply = "learn", f"Learning logged: {topic}."
    write_json(SEEN, z); refresh(); out({"action": act, "reply": reply})

def cmd_ack():
    if today().isoformat() not in {e["date"] for e in ledger_events() if e["type"] == "ack_read"}:
        sh("python3", "scripts/log_event.py", "ack_read"); refresh()
    out({"action": "ack_read"})

def cmd_decide(slot, force):
    s = state(); z = seen()
    if not s["started"] or s["finished"]:
        slot_ = slot or pick_slot({"day_type": "weekend"}, force)
        if slot_ == "morning" and not s["started"] and "pre" not in z["posted"].get(today().isoformat(), []):
            return out({"post": True, "slot": "pre", "message": f"Challenge starts {C['start']}. Get your setup ready: lets-dsa open, digest bookmarked."})
        return out({"post": False, "reason": "outside challenge window"})
    slot = slot or pick_slot(s, force)
    if not slot: return out({"post": False, "reason": "not near a slot"})
    if slot in z["posted"].get(today().isoformat(), []) and not force: return out({"post": False, "reason": "already posted"})
    msg = compose(slot, s); why = visual_reason(slot, s) if msg else None
    if msg and why: msg += f"\nProgress: {C['site_url']}"
    out({"post": bool(msg), "slot": slot, "message": msg, "reason": None if msg else "nothing to say",
         "visual": bool(why), "visual_why": why, "url": C["site_url"]})

def cmd_posted(slot, ts):
    z = seen(); d = today().isoformat(); z["posted"].setdefault(d, []).append(slot)
    if slot == "morning": z["morning_ts"][d] = ts
    write_json(SEEN, z); out({"ok": True})

def cmd_retro():
    s = state(); days = s["days"][-7:]; cnt = {}
    for d in days: cnt[d["rating"]] = cnt.get(d["rating"], 0) + 1
    p = s["pace"]; stale = [c["key"] for c in s["career"] if not c["fresh"]]
    inbox = [l for l in (ROOT / "inbox.md").read_text().splitlines() if l.strip()]
    lines = [f"Week review · {head(s)} · streak {s['streak']} (best {s['best_streak']})",
             "Days: " + ", ".join(f"{k} {v}" for k, v in cnt.items()),
             f"DSA {p['solved']}/{p['goal']} ({p['ahead_by']:+} vs plan). Need {p['needed_per_day']}/day from here.",
             f"Learn entries: {s['metrics']['learn_total']} · gold days: {s['metrics']['gold_days']}"]
    if stale: lines.append("Stale career checks: " + ", ".join(stale))
    if p["needed_per_day"] > 1.5: lines.append("Pace is behind: plan a weekend catch-up.")
    if inbox: lines.append(f"{len(inbox)} rule(s) waiting in inbox.md: run Claude locally to fold them into config.")
    lines.append(f"Progress: {C['site_url']}")
    out({"post": True, "message": "\n".join(lines), "visual": C["visual"]["weekly_review"], "visual_why": "weekly review", "url": C["site_url"]})

def cmd_finish():
    refresh(); sh("git", "add", "-A")
    if sh("git", "diff", "--cached", "--quiet").returncode == 0: return out({"committed": False})
    sh("git", "commit", "-q", "-m", f"tick {now().strftime('%Y-%m-%d %H:%M')}")
    branch = sh("git", "branch", "--show-current").stdout.strip()
    r = sh("git", "push", "-q", "origin", "HEAD")
    res = {"committed": True, "branch": branch, "pushed": r.returncode == 0, "err": r.stderr[-200:]}
    # Routines may only push claude/* branches; .github/workflows/auto-merge-routine.yml opens the PR and merges it.
    # (the routine sandbox has no gh; the workflow opens + merges the PR on push)
    if res["pushed"] and branch.startswith("claude/") and shutil.which("gh"):
        pr = sh("gh", "pr", "create", "--base", "main", "--head", branch,
                "--title", f"tick {now().strftime('%Y-%m-%d %H:%M')}", "--body", "Automated routine state update.")
        res["pr"] = (pr.stdout or pr.stderr).strip()[-200:]
    out(res)

if __name__ == "__main__":
    a = sys.argv[1:]; c = a[0] if a else ""
    if c == "start": cmd_start()
    elif c == "ingest": cmd_ingest(a[1], a[2])
    elif c == "ack": cmd_ack()
    elif c == "decide": cmd_decide(a[a.index("--slot") + 1] if "--slot" in a else None, "--force" in a)
    elif c == "posted": cmd_posted(a[1], a[2])
    elif c == "retro": cmd_retro()
    elif c == "finish": cmd_finish()
    else: raise SystemExit(__doc__)
