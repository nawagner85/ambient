"""Rain soon (interrupt): dry now, but rain expected within the next hour (Open-Meteo 15-minute nowcast).
options: lat, lon, min_mm (0.1 per 15 min), ahead_minutes (60). The id (start slot) makes it fire once per shower."""
from datetime import datetime, timedelta

TTL = 300
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Rain soon',
 'category': 'Alerts',
 'about': 'Cuts in when rain is expected within the hour.',
 'settings': [{'key': 'lat',
               'label': 'Latitude',
               'type': 'number',
               'help': 'Blank = the home location (Integrations → Location)'},
              {'key': 'lon', 'label': 'Longitude', 'type': 'number'},
              {'key': 'min_mm', 'label': 'Rain counts at (mm per 15 min)', 'type': 'number'},
              {'key': 'ahead_minutes', 'label': 'Look ahead (minutes)', 'type': 'number'}]}


def fetch(ctx, opts):
    if opts.get("lat") in (None, "") or opts.get("lon") in (None, ""):
        return None  # no home location yet (admin → Integrations, or Home Assistant's)
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={opts['lat']}&longitude={opts['lon']}"
           "&minutely_15=precipitation&forecast_minutely_15=8&past_minutely_15=1&timezone=America%2FLos_Angeles")
    d = None
    for _ in range(2):  # api.open-meteo.com handshakes time out now and then
        try:
            d = ctx.memo(("rain", url), 600, lambda: ctx.http_json(url, timeout=20))
            break
        except Exception:
            continue
    if not d:
        return None
    m = d["minutely_15"]
    now = ctx.now().replace(tzinfo=None)
    slots = [(datetime.fromisoformat(t), p or 0) for t, p in zip(m["time"], m["precipitation"])]
    past = [p for t, p in slots if t <= now]
    if past and past[-1] >= float(opts.get("min_mm", 0.1)):
        return None  # already raining
    ahead = [(t, p) for t, p in slots if now < t <= now + timedelta(minutes=int(opts.get("ahead_minutes", 60)))]
    start = next(((t, p) for t, p in ahead if p >= float(opts.get("min_mm", 0.1))), None)
    if not start:
        return None
    total = sum(p for t, p in ahead if t >= start[0])
    mins = max(0, int((start[0] - now).total_seconds() // 60))
    return {"id": start[0].strftime("%Y%m%d%H"), "at": start[0].strftime("%-I:%M %p"), "mins": mins,
            "heavy": total >= 2.5, "series": [round(p, 2) for t, p in slots if t > now]}
