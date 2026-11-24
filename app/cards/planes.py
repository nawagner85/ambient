"""Planes card (interrupt): the nearest plane from sensor.nearest_plane (HA package planes_overhead.yaml)
when it is at least min_elevation degrees up. options: entity, min_elevation (30)."""
TTL = 10
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Planes overhead',
 'category': 'Alerts',
 'needs': ['ha'],
 'about': 'Cuts in when a plane is high overhead (HA planes_overhead sensor).',
 'settings': [{'key': 'entity', 'label': 'Nearest-plane sensor', 'type': 'entity', 'domain': 'sensor'},
              {'key': 'min_elevation', 'label': 'At least (degrees up)', 'type': 'number'}]}


def fetch(ctx, opts):
    s = ctx.state(opts.get("entity", "sensor.nearest_plane"))
    if not s or s["state"] in ("none", "unknown", "unavailable"):
        return None
    a = s["attributes"]
    try:
        elev = int(a.get("elevation_deg") or 0)
    except (TypeError, ValueError):
        elev = 0
    if elev < int(opts.get("min_elevation", 30)):
        return None
    keep = ("hex", "flight", "airline", "owner", "origin", "destination", "route", "aircraft", "registration",
            "type_code", "altitude_ft", "speed_kt", "distance_nm", "bearing", "elevation_deg", "photo", "planes_in_range")
    d = {k: a.get(k) for k in keep}
    d["callsign"] = s["state"]
    return d
