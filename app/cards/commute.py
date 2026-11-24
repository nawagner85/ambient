"""Commute card: drive times from HA Waze Travel Time sensors, with how far over a normal drive they are.

options: routes: [{name, to, entity}], baseline_days (7). The "normal" drive is the fastest reading in the
last baseline_days, so a new sensor needs a few days before the delay is meaningful.
"""
TTL = 120
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Commute',
 'category': 'Home',
 'needs': ['ha'],
 'about': 'Drive times from HA Waze Travel Time sensors, compared with a normal drive.',
 'settings': [{'key': 'routes',
               'label': 'Routes',
               'type': 'list',
               'item': 'name',
               'fields': [{'key': 'name', 'label': 'Who', 'type': 'text'},
                          {'key': 'to', 'label': 'To', 'type': 'text'},
                          {'key': 'entity', 'label': 'Travel-time sensor', 'type': 'entity', 'domain': 'sensor'}]},
              {'key': 'baseline_days', 'label': 'Normal drive = fastest in the last N days', 'type': 'number'}]}


def _baseline(ctx, entity, days):
    def get():
        vals = []
        for h in ctx.history(entity, days * 24):
            try:
                vals.append(float(h["state"]))
            except (KeyError, TypeError, ValueError):
                pass
        return min(vals) if vals else None
    return ctx.memo(("baseline", entity), 3600, get)


def _via(route):
    """'I-405 S Exp Toll Ln; I-405 S' -> 'I-405 S (express)'"""
    out, express = [], False
    for part in (p.strip() for p in route.split(";")):
        if "Exp Toll" in part or "Express" in part:
            express = True
            part = part.replace(" Exp Toll Ln", "").replace(" Express Lanes", "").strip()
        if part and part not in out:
            out.append(part)
    return " → ".join(out[:2]) + (" (express)" if express else "")


def fetch(ctx, opts):
    out = []
    for r in opts.get("routes", []):
        s = ctx.state(r["entity"])
        try:
            mins = float(s["state"])
        except (TypeError, ValueError, KeyError):
            continue
        base = _baseline(ctx, r["entity"], int(opts.get("baseline_days", 7))) or mins
        base = min(base, mins)
        ratio = mins / base if base else 1
        out.append({"name": r["name"], "to": r.get("to", ""), "minutes": round(mins), "normal": round(base),
                    "delay": round(mins - base), "level": "ok" if ratio < 1.15 else "slow" if ratio < 1.4 else "bad",
                    "via": _via(s["attributes"].get("route") or ""),
                    "arrive": (ctx.now().timestamp() + mins * 60)})
    return {"routes": out} if out else None
