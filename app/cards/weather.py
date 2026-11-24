"""Weather card: current conditions + daily forecast from a HA weather entity. options: entity, days (5)."""
TTL = 600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Weather',
 'category': 'Weather & sky',
 'needs': ['ha'],
 'about': 'Current conditions and the daily forecast from a Home Assistant weather entity.',
 'settings': [{'key': 'entity', 'label': 'Weather entity', 'type': 'entity', 'domain': 'weather'},
              {'key': 'days', 'label': 'Forecast days', 'type': 'number'}]}


def fetch(ctx, opts):
    e = opts.get("entity", "weather.forecast_home")
    s = ctx.state(e)
    if not s or s["state"] in ("unknown", "unavailable"):
        return None
    a = s["attributes"]
    try:
        r = ctx.service("weather", "get_forecasts", {"entity_id": e, "type": "daily"}, response=True)
        fc = r["service_response"][e]["forecast"]
    except Exception:
        fc = []
    days = [{"date": f["datetime"], "cond": f.get("condition"), "hi": f.get("temperature"),
             "lo": f.get("templow"), "precip": f.get("precipitation_probability")} for f in fc[: int(opts.get("days", 5))]]
    return {"cond": s["state"], "temp": a.get("temperature"), "unit": a.get("temperature_unit", "°F"),
            "humidity": a.get("humidity"), "wind": a.get("wind_speed"), "wind_unit": a.get("wind_speed_unit", ""),
            "place": a.get("friendly_name", ""), "days": days}
