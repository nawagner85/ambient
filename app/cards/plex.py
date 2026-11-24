"""New on Plex: most recently added movies and shows (episodes grouped by show) from your Plex server.
Posters go through /x/<card>/<n> (asset()), so the Plex token stays on the server.
server + token: Integrations → Plex (PLEX_URL, PLEX_TOKEN); options:, count (6), days (21: hide the card if nothing newer)."""
import json
import time
import urllib.parse
import urllib.request

TTL = 900
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'New on Plex',
 'category': 'Media',
 'needs': ['plex'],
 'about': 'Recently added movies and shows on your Plex server.',
 'settings': [{'key': 'count', 'label': 'Titles', 'type': 'number'},
              {'key': 'days', 'label': 'Added in the last (days)', 'type': 'number'}]}


def _get(ctx, opts, path, accept="application/json"):
    url = (ctx.secret("PLEX_URL") or opts.get("url", "")).rstrip("/") + path
    req = urllib.request.Request(url, headers={"X-Plex-Token": ctx.secret("PLEX_TOKEN"), "Accept": accept})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(), r.headers.get("Content-Type", "")


def _recent(ctx, opts):
    def get():
        b, _ = _get(ctx, opts, "/library/recentlyAdded?X-Plex-Container-Start=0&X-Plex-Container-Size=60")
        out, seen = [], set()
        for m in json.loads(b)["MediaContainer"].get("Metadata", []):
            if m.get("type") == "movie":
                key, title, sub, thumb = m["ratingKey"], m["title"], str(m.get("year", "")), m.get("thumb")
            elif m.get("type") in ("episode", "season"):
                show = m.get("grandparentTitle") or m.get("parentTitle") or m.get("title")
                key = "show:" + show
                title = show
                sub = (f"S{m.get('parentIndex', 0):02d}E{m.get('index', 0):02d} · {m.get('title', '')}"
                       if m.get("type") == "episode" else m.get("title", ""))
                thumb = m.get("grandparentThumb") or m.get("parentThumb") or m.get("thumb")
            elif m.get("type") == "show":
                key, title, sub, thumb = "show:" + m["title"], m["title"], "New show", m.get("thumb")
            else:
                continue
            if key in seen or not thumb:
                continue
            seen.add(key)
            out.append({"title": title, "sub": sub, "thumb": thumb, "added": m.get("addedAt", 0),
                        "kind": "Movie" if m.get("type") == "movie" else "TV"})
        return out
    return ctx.memo(("plex-recent",), 900, get)


def asset(ctx, opts, key):
    item = _recent(ctx, opts)[int(key)]
    q = urllib.parse.urlencode({"width": 342, "height": 513, "minSize": 1, "upscale": 1, "url": item["thumb"]})
    return ctx.memo(("plex-img", item["thumb"]), 86400, lambda: _get(ctx, opts, "/photo/:/transcode?" + q, "image/jpeg"))


def fetch(ctx, opts):
    items = _recent(ctx, opts)
    now = time.time()
    fresh = [(i, x) for i, x in enumerate(items) if now - x["added"] < int(opts.get("days", 21)) * 86400]
    if not fresh:
        return None
    out = []
    for i, x in fresh[: int(opts.get("count", 6))]:
        d = int((now - x["added"]) // 86400)
        out.append({"title": x["title"], "sub": x["sub"], "kind": x["kind"],
                    "ago": "today" if d == 0 else "yesterday" if d == 1 else f"{d} days ago",
                    "poster": f"x/{opts['_card']}/{i}"})
    return {"items": out}
