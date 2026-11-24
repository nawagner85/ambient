"""Scores: your teams' games from ESPN's public site API (no key). Shown only when something is worth showing:
a live game, a final from the last `recent_hours`, or a game starting within `upcoming_hours`.

options: teams: [{sport, league, team (ESPN abbreviation or id), name}], recent_hours (18), upcoming_hours (30).
"""
from datetime import datetime, timedelta, timezone

TTL = 120
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Scores',
 'category': 'Sports',
 'about': 'Live games, recent finals and games about to start (ESPN, no key).',
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
              {'key': 'recent_hours', 'label': 'Show finals for (hours)', 'type': 'number'},
              {'key': 'upcoming_hours', 'label': 'Show upcoming within (hours)', 'type': 'number'}]}
API = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team}"


def _game(ctx, t):
    d = ctx.memo(("espn", t["league"], t["team"]), 90, lambda: ctx.http_json(API.format(**t)))["team"]
    ev = (d.get("nextEvent") or [None])[0]
    if not ev:
        return None
    c = ev["competitions"][0]
    st = c["status"]["type"]
    start = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    state = st["state"]  # pre | in | post
    if state == "post" and now - start > timedelta(hours=4 + t.get("recent_hours", 18)):
        return None
    if state == "pre" and start - now > timedelta(hours=t.get("upcoming_hours", 30)):
        return None
    sides = []
    for x in sorted(c["competitors"], key=lambda x: x.get("homeAway") != "away"):  # away first
        sc = x.get("score")
        sc = sc.get("displayValue") if isinstance(sc, dict) else sc
        tm = x["team"]
        logo = tm.get("logos", [{}])[0].get("href") if tm.get("logos") else tm.get("logo")
        sides.append({"abbr": tm.get("abbreviation"), "name": tm.get("shortDisplayName") or tm.get("displayName"),
                      "logo": logo, "score": sc, "ours": str(tm.get("id")) == str(d["id"]),
                      "winner": bool(x.get("winner")), "record": (x.get("record") or [{}])[0].get("displayValue")
                      if isinstance(x.get("record"), list) else None})
    local = start.astimezone(ctx.tz)
    when = local.strftime("%-I:%M %p") if local.date() == ctx.now().date() else local.strftime("%a %-I:%M %p")
    return {"team": t.get("name") or d["displayName"], "state": state, "detail": st.get("shortDetail", ""),
            "when": when, "start": start.timestamp(), "sides": sides,
            "broadcast": ", ".join(b for x in c.get("broadcasts", []) for b in x.get("names", []))}


def fetch(ctx, opts):
    games = []
    for t in opts.get("teams", []):
        t = dict(t, recent_hours=opts.get("recent_hours", 18), upcoming_hours=opts.get("upcoming_hours", 30))
        try:
            g = _game(ctx, t)
        except Exception:
            g = None
        if g:
            games.append(g)
    order = {"in": 0, "post": 1, "pre": 2}
    games.sort(key=lambda g: (order[g["state"]], g["start"]))
    return {"games": games[:4]} if games else None
