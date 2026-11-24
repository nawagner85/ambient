"""Breaking news (interrupt): a top-3 Google News story published in the last `fresh_minutes` that the free LLM
(gemma4:31b-cloud) judges to be genuinely major breaking news. One judgement per headline (cached a day).
options: fresh_minutes (40)."""
import re
from news import items, split_source, GOOGLE

TTL = 120
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Breaking news',
 'category': 'Alerts',
 'needs': ['llm'],
 'about': 'Cuts in when the LLM judges a fresh top story to be major breaking news.',
 'settings': [{'key': 'fresh_minutes', 'label': 'Story younger than (minutes)', 'type': 'number'}]}
PROMPT = ("You decide what interrupts a family's living-room display. Is this headline MAJOR breaking news that most people in a "
          "US household (Seattle area) would want to know about immediately — e.g. a major disaster or attack, war breaking out, "
          "death of a world-famous person, a presidential/national election result, a huge market crash, a major event in the "
          "Seattle area (earthquake, big storm, major closure)? Routine politics, business, sports results, celebrity gossip, "
          "analysis and ongoing stories are NOT breaking. Headline: \"{t}\" ({s}). Answer exactly YES or NO.")


def fetch(ctx, opts):
    now = ctx.now().timestamp()
    for x in items(ctx, GOOGLE, ttl=120)[:3]:
        if now - x["ts"] > int(opts.get("fresh_minutes", 40)) * 60:
            continue
        title, src = split_source(x["title"])
        yes = ctx.memo(("breaking", title), 86400,
                       lambda: re.sub(r"[^A-Z]", "", ctx.llm(PROMPT.format(t=title, s=x["source"] or src),
                                                               max_tokens=5, temperature=0).upper()).startswith("YES"))
        if yes:
            return {"id": title, "title": title, "source": x["source"] or src, "mins": int((now - x["ts"]) // 60)}
    return None
