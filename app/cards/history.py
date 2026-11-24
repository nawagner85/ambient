"""This day in history: Wikipedia's "selected" anniversaries for today; the free LLM picks the most interesting
family-friendly ones (discoveries, firsts, culture, space, sport — no wars/massacres/disasters) once a day.
options: count (3)."""
import json
import re

TTL = 3600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'This day in history',
 'category': 'News & info',
 'needs': ['llm'],
 'about': 'Family-friendly anniversaries from Wikipedia, picked by the LLM.',
 'settings': [{'key': 'count', 'label': 'Events', 'type': 'number'}]}


def fetch(ctx, opts):
    now = ctx.now()
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{now:%m}/{now:%d}"
    n = int(opts.get("count", 3))

    def pick():
        ev = ctx.http_json(url, headers={"User-Agent": "ambient (home display)"}).get("selected", [])
        lines = "\n".join(f"{i}. {e['year']}: {e['text']}" for i, e in enumerate(ev))
        ans = ctx.llm("Pick the " + str(n) + " most interesting, family-friendly events for a living-room display (prefer "
                      "discoveries, inventions, space, firsts, culture, sport, nature; EXCLUDE wars, battles, killings, massacres, "
                      "disasters, terrorism, executions, coups). Reply with only the numbers, comma-separated.\n\n" + lines,
                      max_tokens=20, temperature=0)
        idx = [int(x) for x in re.findall(r"\d+", ans) if int(x) < len(ev)][:n]
        out = []
        for i in idx:
            e = ev[i]
            img = next((p.get("thumbnail", {}).get("source") for p in e.get("pages", []) if p.get("thumbnail")), None)
            out.append({"year": e["year"], "text": e["text"], "img": img, "ago": now.year - e["year"]})
        return out
    items = ctx.memo(("history", now.date().isoformat()), 86400, pick)
    return {"date": now.strftime("%B %-d"), "items": items} if items else None
