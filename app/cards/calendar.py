"""Coming up: next events from HA calendars (Google "Our crazy life"), with US holidays as lighter entries.
options: calendars [{entity, kind: "main"|"holiday"}], days (30), count (5). Hidden when nothing is coming up."""
import urllib.parse
from datetime import date, datetime, timedelta

TTL = 600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Calendar',
 'category': 'Home',
 'needs': ['ha'],
 'about': 'Upcoming events from Home Assistant calendars.',
 'settings': [{'key': 'calendars',
               'label': 'Calendars',
               'type': 'list',
               'item': 'entity',
               'fields': [{'key': 'entity', 'label': 'Calendar', 'type': 'entity', 'domain': 'calendar'},
                          {'key': 'kind', 'label': 'Style', 'type': 'select', 'choices': ['main', 'holiday']}]},
              {'key': 'days', 'label': 'Look ahead (days)', 'type': 'number'},
              {'key': 'count', 'label': 'Events shown', 'type': 'number'}]}


def _events(ctx, entity, start, end):
    q = urllib.parse.urlencode({"start": start.isoformat(), "end": end.isoformat()})
    return ctx.memo(("cal", entity, start.date().isoformat()), 600, lambda: ctx.ha(f"calendars/{entity}?{q}"))


def fetch(ctx, opts):
    now = ctx.now()
    end = now + timedelta(days=int(opts.get("days", 30)))
    today = now.date()
    out = []
    for c in opts.get("calendars", []):
        for e in _events(ctx, c["entity"], now.replace(hour=0, minute=0, second=0, microsecond=0), end):
            s = e["start"]
            if "dateTime" in s:
                st = datetime.fromisoformat(s["dateTime"]).astimezone(ctx.tz)
                en = datetime.fromisoformat(e["end"]["dateTime"]).astimezone(ctx.tz)
                if en < now:
                    continue
                d, time = st.date(), st.strftime("%-I:%M %p")
            else:
                d, time = date.fromisoformat(s["date"]), ""
                if date.fromisoformat(e["end"]["date"]) <= today:
                    continue
            days = (d - today).days
            when = ("Today" if days <= 0 else "Tomorrow" if days == 1 else d.strftime("%A") if days < 7
                    else d.strftime("%a %b %-d"))
            out.append({"title": e["summary"], "when": when, "time": time, "days": max(days, 0),
                        "date": d.isoformat(), "sort": d.isoformat() + (time and "T" + st.strftime("%H:%M") or ""),
                        "kind": c.get("kind", "main"), "where": (e.get("location") or "").split(",")[0][:40],
                        "month": d.strftime("%b").upper(), "dom": d.day})
    out.sort(key=lambda x: (x["sort"], x["kind"] != "main"))
    out = out[: int(opts.get("count", 5))]
    if not any(x["kind"] == "main" for x in out):
        return None  # holidays alone aren't worth a card
    return {"events": out}
