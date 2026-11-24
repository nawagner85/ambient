"""Now playing (interrupt): when one of the listed Music Assistant players is playing, show the track with album
art. Cuts in once per track (client repeat key = title|artist). options: players [{entity, room}].
Album art comes through /x/<card>/<n> (asset() below), so the Shows never need HA auth."""
import time
import urllib.request

TTL = 5
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Now playing',
 'category': 'Media',
 'needs': ['ha'],
 'about': 'Cuts in with album art when a player starts a track.',
 'settings': [{'key': 'players',
               'label': 'Players',
               'type': 'list',
               'item': 'room',
               'fields': [{'key': 'entity', 'label': 'Media player', 'type': 'entity', 'domain': 'media_player'},
                          {'key': 'room', 'label': 'Room', 'type': 'text'}]}]}


def _playing(ctx, opts):
    for i, p in enumerate(opts.get("players", [])):
        s = ctx.state(p["entity"])
        if s and s["state"] == "playing" and s["attributes"].get("media_title"):
            return i, p, s
    return None, None, None


def asset(ctx, opts, key):
    """Album art of player #key (its entity_picture: MA imageproxy URL or HA's media_player_proxy path)."""
    p = opts.get("players", [])[int(key)]
    s = ctx.state(p["entity"])
    pic = (s or {}).get("attributes", {}).get("entity_picture")
    if not pic:
        raise RuntimeError("no art")
    url = pic if pic.startswith("http") else ctx.ha_url + pic

    def get():
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + ctx.ha_token} if not pic.startswith("http") else {})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read(), r.headers.get("Content-Type", "image/jpeg")
    return ctx.memo(("art", url), 600, get)


def fetch(ctx, opts):
    i, p, s = _playing(ctx, opts)
    if s is None:
        return None
    a = s["attributes"]
    pos, dur = a.get("media_position"), a.get("media_duration")
    if pos is not None and a.get("media_position_updated_at"):
        from datetime import datetime
        try:
            pos += time.time() - datetime.fromisoformat(a["media_position_updated_at"]).timestamp()
        except ValueError:
            pass
    title, artist = a.get("media_title"), a.get("media_artist") or ""
    return {"id": f"{title}|{artist}", "title": title, "artist": artist, "album": a.get("media_album_name") or "",
            "room": p.get("room", ""), "art": f"x/{opts['_card']}/{i}?t={abs(hash(title)) % 100000}" if a.get("entity_picture") else None,
            "pos": pos, "dur": dur, "at": time.time()}
