"""Photo card: a deck of random photos from an Immich album, faces kept in frame, portraits paired.

options: album (id), deck (photos per fetch, default 24), exclude_prefixes (file names to skip, e.g. Emi
episodes, which have their own card), pair_portraits (default true: two portraits side by side).
The browser takes one slide at a time from the deck and fetches a new deck when it runs out.
"""
from concurrent.futures import ThreadPoolExecutor

TTL = 0  # every fetch is a fresh random deck
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Photos',
 'category': 'Photos',
 'needs': ['immich'],
 'about': 'Random photos from an Immich album, faces kept in frame. Each view picks its own album.',
 'settings': [{'key': 'album',
               'label': 'Default album',
               'type': 'album',
               'help': "Used by views that don't pick one"},
              {'key': 'deck', 'label': 'Photos per batch', 'type': 'number'},
              {'key': 'pair_portraits', 'label': 'Pair portrait photos side by side', 'type': 'bool'},
              {'key': 'exclude_prefixes', 'label': 'Skip files starting with', 'type': 'tags'}]}


def _faces(ctx, asset_id):
    def get():
        try:
            fs = ctx.immich(f"faces?id={asset_id}")
        except Exception:
            return None
        boxes = [(f["boundingBoxX1"] / f["imageWidth"], f["boundingBoxY1"] / f["imageHeight"],
                  f["boundingBoxX2"] / f["imageWidth"], f["boundingBoxY2"] / f["imageHeight"])
                 for f in fs if f.get("imageWidth") and f.get("imageHeight")]
        if not boxes:
            return None
        x1, y1 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x2, y2 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        return [round((x1 + x2) / 2 * 100), round((y1 + y2) / 2 * 100)]
    return ctx.memo(("faces", asset_id), 86400, get)


def _photo(ctx, a):
    e = a.get("exifInfo") or {}
    w, h = e.get("exifImageWidth") or 0, e.get("exifImageHeight") or 0
    if str(e.get("orientation") or "") in ("5", "6", "7", "8"):
        w, h = h, w
    when = e.get("dateTimeOriginal") or a.get("fileCreatedAt") or ""
    label = ""
    if when[:4].isdigit():
        import datetime
        try:
            label = datetime.date(int(when[:4]), int(when[5:7]), 1).strftime("%B %Y")
        except ValueError:
            label = when[:4]
    place = ", ".join(x for x in (e.get("city"), e.get("state")) if x)
    return {"src": ctx.img(a["id"]), "portrait": bool(w and h and h > w * 1.05),
            "focus": _faces(ctx, a["id"]), "date": label, "place": place}


def fetch(ctx, opts):
    if not opts.get("album"):
        return None  # no album picked yet (view or Photos card settings)
    n = int(opts.get("deck", 24))
    skip = tuple(opts.get("exclude_prefixes", []))
    assets = ctx.immich("search/random", {"albumIds": [opts["album"]], "size": n + 10, "type": "IMAGE", "withExif": True})
    assets = [a for a in assets if not (skip and (a.get("originalFileName") or "").startswith(skip))][:n]
    with ThreadPoolExecutor(6) as pool:
        photos = list(pool.map(lambda a: _photo(ctx, a), assets))
    slides, held = [], None
    for p in photos:
        if opts.get("pair_portraits", True) and p["portrait"]:
            if held:
                slides.append({"photos": [held, p]})
                held = None
            else:
                held = p
        else:
            slides.append({"photos": [p]})
    if held:
        slides.append({"photos": [held]})
    return {"slides": slides} if slides else None
