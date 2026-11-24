"""Live webcams, muted video, "follow the sun": one cam per appearance, among the cams where it is daytime now.

options: cams: [{id, name, place, tz, lat, lon, src}], daylight (true), min_sun (degrees, default -2)
  src: {"youtube": "<live video id>"}   — muted embedded player (all ids checked playableInEmbed 2026-11-23)
       {"hls": "<.m3u8 url>"}           — muted <video> via hls.js (/vendor/hls.light.min.js); needs CORS
       {"image": "<still url>"}         — refreshed every 30 s through the /cam proxy
Live video ids change when a channel restarts its stream: if a cam goes dark, look up the new id on the channel's
/streams page and update config.json.
"""
import math
from datetime import datetime, timezone

TTL = 20
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'heavy': True,  # live video: skipped on low-power views
 'title': 'Webcams',
 'category': 'Webcams',
 'about': "Live muted video, following the sun: only cams where it's daytime.",
 'settings': [{'key': 'daylight', 'label': 'Only cams in daylight', 'type': 'bool'},
              {'key': 'min_sun', 'label': 'Sun at least (degrees)', 'type': 'number'},
              {'key': 'cams',
               'label': 'Cams',
               'type': 'list',
               'item': 'name',
               'fields': [{'key': 'id', 'label': 'Id', 'type': 'text', 'help': 'unique, a-z 0-9 -'},
                          {'key': 'name', 'label': 'Name', 'type': 'text'},
                          {'key': 'place', 'label': 'Caption', 'type': 'text'},
                          {'key': 'src.youtube', 'label': 'YouTube live id', 'type': 'text'},
                          {'key': 'src.hls', 'label': 'HLS .m3u8 URL', 'type': 'text'},
                          {'key': 'src.image', 'label': 'Still image URL', 'type': 'text'},
                          {'key': 'lat', 'label': 'Latitude', 'type': 'number'},
                          {'key': 'lon', 'label': 'Longitude', 'type': 'number'},
                          {'key': 'tz', 'label': 'Time zone', 'type': 'text', 'help': 'e.g. America/Los_Angeles'}]}]}
_turn = {"i": 0}


def sun_elevation(lat, lon, when=None):
    """Solar elevation in degrees (NOAA approximation, good to ~1°)."""
    t = when or datetime.now(timezone.utc)
    doy = t.timetuple().tm_yday
    hour = t.hour + t.minute / 60
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                    - 0.040849 * math.sin(2 * g))
    tst = hour * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cosz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1, min(1, cosz))))


def cam_image(ctx, cam):
    """(bytes, content type) for still-image cams (server.py /cam/<id> proxy)."""
    import urllib.request

    def get():
        req = urllib.request.Request(cam["src"]["image"], headers={"User-Agent": "Mozilla/5.0 (ambient)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read(), r.headers.get("Content-Type", "image/jpeg")
    return ctx.memo(("still", cam["src"]["image"]), 30, get)


def fetch(ctx, opts):
    cams = opts.get("cams", [])
    lit = [c for c in cams if not opts.get("daylight", True) or "lat" not in c
           or sun_elevation(c["lat"], c["lon"]) > opts.get("min_sun", -2)]
    if not lit:
        return None
    cam = lit[_turn["i"] % len(lit)]
    _turn["i"] += 1
    now = datetime.now(timezone.utc)
    local = ""
    if cam.get("tz"):
        from zoneinfo import ZoneInfo
        local = now.astimezone(ZoneInfo(cam["tz"])).strftime("%-I:%M %p")
    src = cam["src"]
    kind = "youtube" if "youtube" in src else "hls" if "hls" in src else "image"
    out = {"id": cam["id"], "name": cam["name"], "place": cam.get("place", ""), "local": local, "kind": kind}
    out["src"] = (src["youtube"] if kind == "youtube" else src["hls"] if kind == "hls"
                  else f"cam/{cam['id']}?t={int(now.timestamp() // 30)}")
    return out
