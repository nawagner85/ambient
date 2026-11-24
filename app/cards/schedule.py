"""Upcoming games: the next game for each of your teams in the next `days`, with start time and TV channel
(ESPN team schedule API, no key). options: teams (same list as scores), days (7), max (6)."""
from datetime import datetime, timedelta, timezone

TTL = 1800
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Upcoming games',
 'category': 'Sports',
 'about': 'Next game per team with time and TV channel (ESPN).',
 'settings': [{'key': 'teams',
               'label': 'Teams',
               'type': 'list',
               'item': 'name',
               'fields': [{'key': 'name', 'label': 'Name', 'type': 'text'},
                          {'key': 'sport',
                           'label': 'Sport',
                           'type': 'select',
                           'choices': ['baseball', 'football', 'basketball', 'hockey', 'soccer']},
                          {'key': 'league',
                           'label': 'League',
                           'type': 'select',
                           'choices': ['mlb',
                                       'nfl',
                                       'nba',
                                       'nhl',
                                       'wnba',
                                       'mls',
                                       'college-football',
                                       'mens-college-basketball']},
                          {'key': 'team',
                           'label': 'ESPN team',
                           'type': 'text',
                           'help': 'Abbreviation (sea, sf) or ESPN id (CSU = 36)'}]},
              {'key': 'days', 'label': 'Look ahead (days)', 'type': 'number'},
              {'key': 'max', 'label': 'Games shown', 'type': 'number'}]}
API = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team}/schedule"


def _next(ctx, t, horizon):
    d = ctx.memo(("espn-sched", t["league"], t["team"]), 1800, lambda: ctx.http_json(API.format(**t)))
    now = datetime.now(timezone.utc)
    me = str(d.get("team", {}).get("id", ""))
    for ev in d.get("events", []):
        start = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
        c = ev["competitions"][0]
        if c["status"]["type"]["state"] != "pre" or start < now or start > horizon:
            continue
        us = next((x for x in c["competitors"] if str(x["team"]["id"]) == me), c["competitors"][0])
        them = next((x for x in c["competitors"] if x is not us), us)
        tv = []
        for b in c.get("broadcasts", []):
            name = (b.get("media") or {}).get("shortName") or ", ".join(b.get("names", []))
            if name and name not in tv:
                tv.append(name)
        local = start.astimezone(ctx.tz)
        today = ctx.now().date()
        day = "Today" if local.date() == today else "Tomorrow" if local.date() == today + timedelta(days=1) else local.strftime("%a %b %-d")
        logo = lambda x: (x["team"].get("logos") or [{}])[0].get("href") or x["team"].get("logo")
        return {"team": t.get("name"), "logo": logo(us), "vs": ("vs " if us.get("homeAway") == "home" else "@ ")
                + (them["team"].get("shortDisplayName") or them["team"].get("displayName")), "opp_logo": logo(them),
                "day": day, "time": local.strftime("%-I:%M %p"), "tv": " · ".join(tv[:2]), "start": start.timestamp(),
                "tbd": bool(c["status"]["type"].get("detail", "").upper().endswith("TBD"))}
    return None


def fetch(ctx, opts):
    horizon = datetime.now(timezone.utc) + timedelta(days=int(opts.get("days", 7)))
    games = []
    for t in opts.get("teams", []):
        try:
            g = _next(ctx, t, horizon)
        except Exception:
            g = None
        if g:
            games.append(g)
    games.sort(key=lambda g: g["start"])
    return {"games": games[: int(opts.get("max", 6))]} if games else None
