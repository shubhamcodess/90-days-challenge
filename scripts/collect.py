#!/usr/bin/env python3
"""Read the other repos (read-only) into data/derived/collected.json.
DSA blobs are cached by sha so only new/changed question files are fetched."""
import sys
from lib import *

def local_clone(repo):
    """The routine sandbox checks out its source repos beside this one; use them if the API refuses."""
    name = repo.split("/")[-1]
    for base in (ROOT.parent, Path.home(), Path.home() / "Development"):
        if (base / name / "questions").is_dir(): return base / name
    return None

def collect_dsa_local(repo, s):
    d = local_clone(repo)
    if not d: raise RuntimeError("API refused and no local clone")
    out = []
    for f in sorted((d / s["path"]).rglob("*.md")):
        fm = front_matter(f.read_text(errors="ignore"))
        if fm.get("status") == "solved" and fm.get("solved_on"):
            out.append({"path": str(f.relative_to(d)), "status": "solved", "solved_on": fm["solved_on"], "title": fm.get("title"),
                        "difficulty": fm.get("difficulty"), "pattern": fm.get("pattern"), "hints_used": fm.get("hints_used")})
    return {"repo": repo, "solved": out, "via": "local clone"}

def collect_dsa():
    p = pillar("dsa"); s = p["source"]; repo = s["repo"]
    try:
        return collect_dsa_api(p, s, repo)
    except Exception as e:
        print(f"[collect] dsa api failed ({e}); trying local clone", file=sys.stderr)
        return collect_dsa_local(repo, s)

def collect_dsa_api(p, s, repo):
    cache_path = ROOT / "data" / "cache" / "dsa.json"
    cache = read_json(cache_path, {})
    tree = gh(f"repos/{repo}/git/trees/{s['ref']}?recursive=1")["tree"]
    seen = {}
    for n in tree:
        path = n["path"]
        if n["type"] != "blob" or not path.startswith(s["path"] + "/") or not path.endswith(".md"):
            continue
        seen[path] = n["sha"]
        if cache.get(path, {}).get("sha") == n["sha"]:
            continue
        fm = front_matter(gh(f"repos/{repo}/contents/{path}?ref={s['ref']}", raw=True))
        cache[path] = {"sha": n["sha"], "status": fm.get("status"), "solved_on": fm.get("solved_on"),
                       "title": fm.get("title"), "difficulty": fm.get("difficulty"), "pattern": fm.get("pattern"),
                       "hints_used": fm.get("hints_used")}
    cache = {k: v for k, v in cache.items() if k in seen}
    write_json(cache_path, cache)
    solved = [dict(v, path=k) for k, v in cache.items() if v.get("status") == "solved" and v.get("solved_on")]
    return {"repo": repo, "solved": solved}

def collect_tech():
    p = pillar("tech"); s = p["source"]
    idx = gh(f"repos/{s['repo']}/contents/{s['index']}", raw=True)
    j = json.loads(idx)
    items = j if isinstance(j, list) else j.get("editions") or j.get("dates") or []
    latest = None
    if items:
        last = items[0] if isinstance(items[0], str) and items[0] > items[-1] else items[-1]
        latest = last if isinstance(last, str) else (last.get("date") or last.get("id"))
    return {"url": s["url"], "latest_edition": latest}

def collect_career():
    p = pillar("career"); repo = p["source"]["repo"]; out = {}
    for c in p["checks"]:
        paths = c.get("auto", {}).get("paths")
        if not paths:
            continue
        latest = None
        for path in paths:
            try:
                r = gh(f"repos/{repo}/commits?path={path}&per_page=1")
            except Exception:
                continue
            if r:
                d = r[0]["commit"]["author"]["date"][:10]
                latest = max(latest, d) if latest else d
        out[c["key"]] = latest
    return out

if __name__ == "__main__":
    res = {"collected_at": now().isoformat(timespec="seconds")}
    for name, fn in [("dsa", collect_dsa), ("tech", collect_tech), ("career", collect_career)]:
        try:
            res[name] = fn()
        except Exception as e:  # one broken source must not kill the run
            res[name] = {"error": str(e)}
            print(f"[collect] {name} failed: {e}", file=sys.stderr)
    write_json(ROOT / "data" / "derived" / "collected.json", res)
    print("collected:", {k: ("error" if isinstance(v, dict) and "error" in v else "ok") for k, v in res.items() if k != "collected_at"})
