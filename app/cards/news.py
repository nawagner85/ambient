"""Top news: Google News US top stories (headline + source), led by the NYT home-page lead story with its photo.
options: count (5). Feeds are public RSS; nothing is sent from here except the requests."""
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

TTL = 600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Top news',
 'category': 'News & info',
 'about': 'Google News US top stories, led by the NYT lead photo.',
 'settings': [{'key': 'count', 'label': 'Headlines', 'type': 'number'}]}
GOOGLE = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
NYT = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
MEDIA = "{http://search.yahoo.com/mrss/}"


def items(ctx, url, ttl=600):
    def get():
        b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read()
        out = []
        for it in ET.fromstring(b).iter("item"):
            img = it.find(MEDIA + "content")
            if img is None:
                img = it.find(MEDIA + "thumbnail")
            try:
                ts = parsedate_to_datetime(it.findtext("pubDate")).timestamp()
            except Exception:
                ts = 0
            out.append({"title": (it.findtext("title") or "").strip(), "ts": ts,
                        "img": img.get("url") if img is not None else None,
                        "source": (it.find("source").text if it.find("source") is not None else "")})
        return out
    return ctx.memo(("rss", url), ttl, get)


def split_source(t):
    m = re.match(r"^(.*) - ([^-]{2,40})$", t)
    return (m.group(1), m.group(2)) if m else (t, "")


def ago(ts, now):
    m = int((now - ts) // 60)
    return f"{m} min ago" if m < 60 else f"{m // 60} h ago" if m < 1440 else ""


def fetch(ctx, opts):
    now = ctx.now().timestamp()
    g = items(ctx, GOOGLE)
    lead = next((x for x in items(ctx, NYT) if x["img"]), None)
    heads = []
    for x in g[: int(opts.get("count", 5)) + 1]:
        title, src = split_source(x["title"])
        heads.append({"title": title, "source": (x["source"] or src).split(" - ")[0], "ago": ago(x["ts"], now)})
    if lead:
        lead = {"title": lead["title"], "source": "The New York Times", "img": lead["img"], "ago": ago(lead["ts"], now)}
    return {"lead": lead, "heads": heads[: int(opts.get("count", 5))]} if heads else None
