"""New on your streaming services (TMDb, token TMDB_TOKEN). kind "movie": recent digital/streaming releases;
kind "tv": shows with episodes airing this week. Filtered to your services (flatrate, US), most popular first,
each tagged with the service it's on. options: kind, providers [TMDb provider ids; pick yours in the admin],
days (30 movie / 3 tv), count (6), skip_genres (tv: talk/news/reality/soap)."""
import urllib.parse
from datetime import date, timedelta

TTL = 3 * 3600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'New on streaming',
 'category': 'Media',
 'needs': ['tmdb'],
 'about': 'New releases on your streaming services (TMDb).',
 'settings': [{'key': 'kind', 'label': 'Kind', 'type': 'select', 'choices': ['movie', 'tv']},
              {'key': 'providers',
               'label': 'Your services',
               'type': 'multi',
               'choices': [[8, 'Netflix'],
                           [1796, 'Netflix (ads)'],
                           [15, 'Hulu'],
                           [2528, 'YouTube TV'],
                           [350, 'Apple TV+'],
                           [9, 'Prime Video'],
                           [2100, 'Prime Video (ads)'],
                           [386, 'Peacock'],
                           [387, 'Peacock Premium'],
                           [337, 'Disney+'],
                           [1899, 'Max'],
                           [531, 'Paramount+'],
                           [283, 'Crunchyroll'],
                           [43, 'Starz'],
                           [526, 'AMC+']]},
              {'key': 'days', 'label': 'Released in the last (days)', 'type': 'number'},
              {'key': 'count', 'label': 'Titles', 'type': 'number'}]}
API = "https://api.themoviedb.org/3/"
IMG = "https://image.tmdb.org/t/p/"
NAMES = {8: "Netflix", 1796: "Netflix", 15: "Hulu", 2528: "YouTube TV", 350: "Apple TV+", 9: "Prime Video",
         2100: "Prime Video", 386: "Peacock", 387: "Peacock", 337: "Disney+"}  # Disney+: Living Room Fire TV only


def tmdb(ctx, path, **q):
    url = API + path + ("?" + urllib.parse.urlencode(q) if q else "")
    return ctx.memo(("tmdb", url), 6 * 3600, lambda: ctx.http_json(
        url, headers={"Authorization": "Bearer " + ctx.secret("TMDB_TOKEN")}))


def fetch(ctx, opts):
    kind = opts.get("kind", "movie")
    prov = [int(p) for p in opts.get("providers", list(NAMES))]
    today = date.today()
    q = dict(watch_region="US", with_watch_providers="|".join(map(str, prov)), with_watch_monetization_types="flatrate",
             sort_by="popularity.desc", language="en-US", include_adult="false")
    if kind == "tv":
        q["without_genres"] = opts.get("skip_genres", "10767|10763|10764|10766")  # talk, news, reality, soap
    if kind == "movie":
        q.update({"release_date.gte": (today - timedelta(days=int(opts.get("days", 30)))).isoformat(),
                  "release_date.lte": today.isoformat(), "with_release_type": "4|5", "region": "US"})
    else:
        q.update({"air_date.gte": (today - timedelta(days=int(opts.get("days", 3)))).isoformat(),
                  "air_date.lte": (today + timedelta(days=4)).isoformat(), "with_original_language": "en"})
    res = tmdb(ctx, f"discover/{kind}", **q).get("results", [])
    out = []
    for r in res:
        if not r.get("poster_path"):
            continue
        wp = tmdb(ctx, f"{kind}/{r['id']}/watch/providers").get("results", {}).get("US", {}).get("flatrate", [])
        mine = [p for p in wp if p["provider_id"] in prov]
        if not mine:
            continue
        out.append({"title": r.get("title") or r.get("name"), "poster": IMG + "w342" + r["poster_path"],
                    "backdrop": IMG + "w780" + r["backdrop_path"] if r.get("backdrop_path") else None,
                    "service": NAMES.get(mine[0]["provider_id"], mine[0]["provider_name"]), "logo": IMG + "w92" + mine[0]["logo_path"],
                    "year": (r.get("release_date") or r.get("first_air_date") or "")[:4],
                    "rating": round(r.get("vote_average") or 0, 1)})
        if len(out) >= int(opts.get("count", 6)):
            break
    return {"kind": kind, "items": out} if out else None
