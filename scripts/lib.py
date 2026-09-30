"""Shared helpers. stdlib only so a cloud routine needs no pip install."""
import base64, datetime as dt, json, os, subprocess, urllib.request, urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent

def cfg(name):
    return json.loads((ROOT / "config" / name).read_text())

def pillar(pid):
    return cfg(f"pillars/{pid}.json")

def tz():
    return ZoneInfo(cfg("challenge.json")["timezone"])

def now():
    return dt.datetime.now(tz())

def today():
    return now().date()

def parse_date(s):
    return dt.date.fromisoformat(s)

def _token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def gh(path, raw=False):
    """GET https://api.github.com/<path>. Returns parsed JSON (or text if raw)."""
    req = urllib.request.Request("https://api.github.com/" + path.lstrip("/"))
    tok = _token()
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Accept", "application/vnd.github.raw+json" if raw else "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return body if raw else json.loads(body)

def front_matter(text):
    out = {}
    if not text.startswith("---"):
        return out
    for line in text.split("---", 2)[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out

def read_json(p, default=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default

def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

def ledger_events():
    ev = []
    for f in sorted((ROOT / "data" / "ledger").glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                ev.append(json.loads(line))
    return ev

def append_event(etype, data, date=None):
    d = date or today().isoformat()
    e = {"ts": now().isoformat(timespec="seconds"), "date": d, "type": etype, "data": data}
    f = ROOT / "data" / "ledger" / f"{d[:7]}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a") as fh:
        fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return e
