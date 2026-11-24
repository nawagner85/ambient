"""Is the mountain out? Space Needle panorama cam, slice 8 (looks south over downtown and the stadiums toward
Mount Rainier; a new frame every 10-20 min), judged by the free vision model (gemma4:31b-cloud).

Validated 2026-11-23 on 28 hand-labelled midday frames (Sep-Nov 2026 + Jul 2025): 28/28 exact with this prompt,
no false mountains (foothills, haze, fog) and no misses. The verdict is cached per frame. Seattle daylight only.
options: lat/lon (daylight check), min_sun (3), slice (8)."""
import base64
import re
import urllib.request
from datetime import timedelta

TTL = 120
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Is the mountain out?',
 'category': 'Webcams',
 'needs': ['llm'],
 'about': 'Space Needle cam toward Rainier, judged by the vision model.',
 'settings': [{'key': 'lat', 'label': 'Daylight check latitude', 'type': 'number'},
              {'key': 'lon', 'label': 'Longitude', 'type': 'number'},
              {'key': 'min_sun', 'label': 'Sun at least (degrees)', 'type': 'number'}]}
BASE = "https://d3omclagh7m7mg.cloudfront.net/assets"
PROMPT = (
    "Webcam view from the Space Needle in Seattle looking south over downtown and the stadiums. On clear days Mount Rainier, a huge "
    "snow-covered volcano, rises above the far horizon. Low dark hills or the Cascade foothills on the horizon are NOT Rainier; Rainier is a "
    "single broad white snowy cone. Rate it:\n"
    "OUT = you can see Rainier's white snowy cone with a recognisable outline (its summit and upper slopes), even if it looks small or the "
    "base is hazy. This is the normal answer for a sunny view of the mountain.\n"
    "PEEKING = only a faint, washed-out ghost of the mountain, or just part of it showing through cloud.\n"
    "HIDING = no mountain.\nReply with exactly one word: OUT, PEEKING or HIDING.")


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
        return r.read(), r.headers.get("Content-Type", "image/jpeg")


def latest(ctx, sl=8):
    """URL of the newest frame: step back from now (Pacific) in 10-minute steps until one exists (3 h max)."""
    def find():
        t = ctx.now().replace(second=0, microsecond=0)
        t -= timedelta(minutes=t.minute % 10)
        for _ in range(18):
            url = f"{BASE}/{t:%Y/%m/%d}/{t:%Y_%m%d_%H%M%S}/slice{sl}.jpg"
            try:
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(req, timeout=10)
                return url, t.strftime("%-I:%M %p")
            except Exception:
                t -= timedelta(minutes=10)
        return None, None
    return ctx.memo(("needle-latest", sl), 300, find)


def cam_image(ctx, cam):
    url, _ = latest(ctx, cam.get("slice", 8))
    if not url:
        raise RuntimeError("no recent Space Needle frame")
    return ctx.memo(("needle", url), 3600, lambda: _get(url))


def _verdict(ctx, img):
    du = "data:image/jpeg;base64," + base64.b64encode(img).decode()
    word = re.sub(r"[^A-Z]", "", ctx.llm(PROMPT, max_tokens=10, image_url=du, temperature=0).upper())
    return "out" if word.startswith("OUT") else "peeking" if word.startswith("PEEK") else "hiding"


def fetch(ctx, opts):
    from webcam import sun_elevation
    if sun_elevation(opts.get("lat", 47.62), opts.get("lon", -122.35)) < opts.get("min_sun", 3):
        return None
    cam = opts["cams"][0]
    url, taken = latest(ctx, cam.get("slice", 8))
    if not url:
        return None
    img, _ = cam_image(ctx, cam)
    state = ctx.memo(("mountain", url), 86400, lambda: _verdict(ctx, img))  # one verdict per frame
    return {"src": f"cam/{cam['id']}?f={url.rsplit('/', 2)[1]}", "name": cam["name"], "taken": taken, "state": state}
