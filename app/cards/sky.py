"""Sky tonight: sun (sunrise/sunset, golden hour, day-length change), moon (phase, illumination, next full/new),
aurora chance (NOAA SWPC planetary Kp forecast; at ~48°N Kp 6+ is a real chance, 5 a maybe).
Sun + moon are computed locally. options: lat, lon."""
import math
from datetime import datetime, timedelta, timezone

from webcam import sun_elevation

TTL = 1800
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Sky',
 'category': 'Weather & sky',
 'about': 'Sun times, moon phase, aurora chance.',
 'settings': [{'key': 'lat',
               'label': 'Latitude',
               'type': 'number',
               'help': 'Blank = the home location (Integrations → Location)'},
              {'key': 'lon', 'label': 'Longitude', 'type': 'number'}]}
SYNODIC = 29.530588853
NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)  # reference new moon


def _cross(lat, lon, day0, rising, elev=-0.833):
    """Minute when the sun crosses elev (rising or setting) during the local day starting at day0 (aware)."""
    prev = sun_elevation(lat, lon, day0.astimezone(timezone.utc))
    for m in range(1, 24 * 60 + 1):
        t = day0 + timedelta(minutes=m)
        e = sun_elevation(lat, lon, t.astimezone(timezone.utc))
        if (rising and prev < elev <= e) or (not rising and prev > elev >= e):
            return t
        prev = e
    return None


def _moon(now):
    age = ((now - NEW_MOON).total_seconds() / 86400) % SYNODIC
    illum = (1 - math.cos(2 * math.pi * age / SYNODIC)) / 2
    names = ["New moon", "Waxing crescent", "First quarter", "Waxing gibbous", "Full moon", "Waning gibbous", "Last quarter", "Waning crescent"]
    name = names[int((age / SYNODIC) * 8 + 0.5) % 8]
    to_full = (SYNODIC / 2 - age) % SYNODIC
    to_new = (SYNODIC - age) % SYNODIC
    return {"age": round(age, 1), "illum": round(illum * 100), "name": name, "waxing": age < SYNODIC / 2,
            "full_in": round(to_full), "new_in": round(to_new),
            "full_date": (now + timedelta(days=to_full)).strftime("%b %-d")}


def fetch(ctx, opts):
    if opts.get("lat") in (None, "") or opts.get("lon") in (None, ""):
        return None  # no home location yet (admin → Integrations, or Home Assistant's)
    lat, lon = opts["lat"], opts["lon"]
    now = ctx.now()
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def sun_for(d0):
        r, s = _cross(lat, lon, d0, True), _cross(lat, lon, d0, False)
        return r, s
    rise, set_ = ctx.memo(("sun", day0.date().isoformat()), 86400, lambda: sun_for(day0))
    prise, pset = ctx.memo(("sun", (day0 - timedelta(days=1)).date().isoformat()), 86400, lambda: sun_for(day0 - timedelta(days=1)))
    golden = ctx.memo(("golden", day0.date().isoformat()), 86400, lambda: _cross(lat, lon, day0, False, 6.0))
    length = (set_ - rise).total_seconds() if rise and set_ else 0
    change = length - ((pset - prise).total_seconds() if prise and pset else length)
    frac = min(1, max(0, (now - rise).total_seconds() / length)) if length and rise <= now <= set_ else (0 if now < rise else 1)
    kp = None
    try:
        rows = ctx.memo(("kp",), 3600, lambda: ctx.http_json("https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"))
        tonight = [r["kp"] for r in rows if r.get("observed") != "observed"
                   and 0 <= (datetime.fromisoformat(r["time_tag"]).replace(tzinfo=timezone.utc) - now.astimezone(timezone.utc)).total_seconds() <= 18 * 3600]
        kp = round(max(tonight), 1) if tonight else None
    except Exception:
        pass
    aurora = None if kp is None else ("Good chance — look north after dark!" if kp >= 6 else "Possible on dark northern horizons" if kp >= 5 else None)
    fmt = lambda t: t.strftime("%-I:%M %p") if t else "—"
    return {"sunrise": fmt(rise), "sunset": fmt(set_), "golden": fmt(golden), "daylight": f"{int(length // 3600)}h {int(length % 3600 // 60)}m",
            "change": f"{'+' if change >= 0 else '−'}{int(abs(change) // 60)}m {int(abs(change) % 60)}s", "sunfrac": round(frac, 3),
            "up": bool(rise and set_ and rise <= now <= set_), "moon": _moon(now.astimezone(timezone.utc)), "kp": kp, "aurora": aurora}
