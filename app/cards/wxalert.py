"""Weather alerts (interrupt): active National Weather Service alerts for the house's (rounded) point.
options: lat, lon, min_severity ("Moderate"), skip (event names to ignore)."""
TTL = 300
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Weather alerts',
 'category': 'Alerts',
 'about': 'National Weather Service alerts for your location (US).',
 'settings': [{'key': 'lat',
               'label': 'Latitude',
               'type': 'number',
               'help': 'Blank = the home location (Integrations → Location)'},
              {'key': 'lon', 'label': 'Longitude', 'type': 'number'},
              {'key': 'min_severity',
               'label': 'Minimum severity',
               'type': 'select',
               'choices': ['Minor', 'Moderate', 'Severe', 'Extreme']},
              {'key': 'skip', 'label': 'Ignore alert types', 'type': 'tags'}]}
RANK = {"Unknown": 0, "Minor": 1, "Moderate": 2, "Severe": 3, "Extreme": 4}


def fetch(ctx, opts):
    if opts.get("lat") in (None, "") or opts.get("lon") in (None, ""):
        return None  # no home location yet (admin → Integrations, or Home Assistant's)
    url = f"https://api.weather.gov/alerts/active?point={opts['lat']},{opts['lon']}"
    d = ctx.memo(("nws", url), 240, lambda: ctx.http_json(url, headers={"User-Agent": "ambient (home display)", "Accept": "application/geo+json"}))
    keep = []
    for f in d.get("features", []):
        p = f["properties"]
        if RANK.get(p.get("severity"), 0) < RANK[opts.get("min_severity", "Moderate")] or p.get("event") in opts.get("skip", []):
            continue
        keep.append(p)
    if not keep:
        return None
    keep.sort(key=lambda p: -RANK.get(p.get("severity"), 0))
    p = keep[0]
    return {"id": p.get("id"), "event": p.get("event"), "severity": p.get("severity"), "headline": p.get("headline") or "",
            "desc": " ".join((p.get("description") or "").split())[:360], "until": p.get("ends") or p.get("expires"),
            "more": len(keep) - 1}
