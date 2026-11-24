"""Zoltar (Chumby tribute): a carnival fortune-teller card. A fresh batch of fortunes each day from the free
LLM (LiteLLM gemma4:31b-cloud), a different one each time the card comes up.
options: per_day (6), extra (a line added to the prompt)."""
import random
import re

TTL = 30
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Zoltar',
 'category': 'Fun',
 'needs': ['llm'],
 'about': 'Fortunes from the LLM, typed out by Zoltar.',
 'settings': [{'key': 'per_day', 'label': 'Fortunes per day', 'type': 'number'},
              {'key': 'extra', 'label': 'Make it yours', 'type': 'textarea', 'help': 'Added to the prompt, e.g. Mention our dog Biscuit, the Mariners and Mount Rainier.'}]}


def _batch(ctx, opts):
    today = ctx.now()
    wx = ctx.state("weather.forecast_home")
    cond = (wx or {}).get("state", "") if wx else ""
    n = int(opts.get("per_day", 6))
    prompt = (
        f"You are Zoltar, a dramatic old carnival fortune-telling machine in a family's living room. "
        f"Today is {today:%A, %B %-d}. The weather is {cond.replace('partlycloudy', 'partly cloudy') or 'unknown'}. "
        f"Write {n} different fortunes, one per line, no numbering, no quotes. Each is 1-2 short sentences (max 28 words), "
        "playful, warm and family-friendly, in a grand mystical voice. Mix in: everyday small wins, food, weekend plans, "
        "pets, coffee, rain, sunshine, "
        "and one lucky number per fortune at the end like 'Lucky number: 7'. No predictions about health, money or danger. "
        + opts.get("extra", "")
    )
    text = ctx.llm(prompt, max_tokens=700)
    lines = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", l).strip().strip('"') for l in text.splitlines()]
    return [l for l in lines if len(l) > 20][:n]


def fetch(ctx, opts):
    day = ctx.now().date().isoformat()
    fortunes = ctx.memo(("zoltar", day), 86400, lambda: _batch(ctx, opts))
    if not fortunes:
        return None
    f = random.choice(fortunes)
    m = re.search(r"Lucky number:?\s*(\d+)\.?$", f, re.I)
    lucky = m.group(1) if m else str(random.randint(1, 99))
    text = re.sub(r"\s*Lucky number:?\s*\d+\.?$", "", f, flags=re.I).strip()
    return {"fortune": text, "lucky": lucky}
