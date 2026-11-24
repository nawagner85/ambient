"""Word of the day: Merriam-Webster's RSS (word, pronunciation, part of speech, definition, example)."""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

TTL = 3600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Word of the day', 'category': 'News & info', 'about': "Merriam-Webster's word of the day.", 'settings': []}
FEED = "https://www.merriam-webster.com/wotd/feed/rss2"


def fetch(ctx, opts):
    def get():
        b = urllib.request.urlopen(urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read()
        it = ET.fromstring(b).find(".//item")
        raw = it.findtext("description") or ""
        raw = re.sub(r"(?i)</p>|<br\s*/?>|</h\d>", "\n", raw)       # paragraph breaks only
        txt = html.unescape(re.sub(r"<[^>]+>", "", raw))
        lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]
        lines = [l for l in lines if l]
        word = (it.findtext("title") or "").strip()
        head = next((l for l in lines if "•" in l), "")             # "optimization • \\ahp-tuh-…\\ • noun"
        parts = [x.strip() for x in head.split("•")]
        pron = parts[1] if len(parts) > 1 else ""
        pos = parts[2] if len(parts) > 2 else ""
        i = lines.index(head) if head in lines else 0
        rest = [l for l in lines[i + 1:] if not l.startswith(("See the entry", "Examples:"))]
        definition = next((l for l in rest if not l.startswith("//")), "")
        example = next((l[2:].strip() for l in rest if l.startswith("//")), "")
        return {"word": word, "pron": pron.replace("\\", "").strip(), "pos": pos, "def": definition[:300], "example": example[:220]}
    d = ctx.memo(("wotd", ctx.now().date().isoformat()), 21600, get)
    return d if d.get("word") else None
