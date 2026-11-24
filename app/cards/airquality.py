"""Air quality: only when it isn't good (US AQI > threshold). Open-Meteo air-quality API (no key).
options: lat, lon, threshold (50), smoke_pm25 (35)."""
TTL = 900
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Air quality',
 'category': 'Weather & sky',
 'about': "Shown only when the AQI is above the threshold; 'Wildfire smoke' when PM2.5 is high.",
 'settings': [{'key': 'lat',
               'label': 'Latitude',
               'type': 'number',
               'help': 'Blank = the home location (Integrations → Location)'},
              {'key': 'lon', 'label': 'Longitude', 'type': 'number'},
              {'key': 'threshold', 'label': 'Show when US AQI above', 'type': 'number'},
              {'key': 'smoke_pm25', 'label': 'Smoke title at PM2.5 ≥ (µg/m³)', 'type': 'number'}]}
CATS = [(50, "Good", "#6FCF97"), (100, "Moderate", "#F2C94C"), (150, "Unhealthy for sensitive groups", "#F2994A"),
        (200, "Unhealthy", "#EB5757"), (300, "Very unhealthy", "#9B51E0"), (9999, "Hazardous", "#7E0023")]


def fetch(ctx, opts):
    if opts.get("lat") in (None, "") or opts.get("lon") in (None, ""):
        return None  # no home location yet (admin → Integrations, or Home Assistant's)
    url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={opts['lat']}&longitude={opts['lon']}"
           "&current=us_aqi,pm2_5&hourly=us_aqi&forecast_days=2&timezone=America%2FLos_Angeles")
    d = ctx.memo(("aqi", url), 600, lambda: ctx.http_json(url))
    aqi = (d.get("current") or {}).get("us_aqi")
    if aqi is None or aqi <= int(opts.get("threshold", 50)):
        return None
    cat = next(c for c in CATS if aqi <= c[0])
    pm = d["current"].get("pm2_5")
    hours = d.get("hourly", {})
    nxt = [v for v in (hours.get("us_aqi") or [])[:24] if v is not None]
    return {"aqi": round(aqi), "cat": cat[1], "color": cat[2], "pm25": pm, "smoke": bool(pm and pm >= float(opts.get("smoke_pm25", 35))),
            "peak": round(max(nxt)) if nxt else None, "trend": [round(v) for v in nxt]}
