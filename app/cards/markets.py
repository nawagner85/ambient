"""US markets: S&P 500, Dow, Nasdaq — last price, change vs previous close, intraday sparkline (Yahoo Finance chart
API, unofficial, no key). options: symbols [{sym, name}]."""
import urllib.parse

TTL = 300
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Markets',
 'category': 'News & info',
 'about': 'Index prices and intraday sparkline (Yahoo Finance).',
 'settings': [{'key': 'symbols',
               'label': 'Symbols',
               'type': 'list',
               'item': 'name',
               'fields': [{'key': 'sym', 'label': 'Ticker', 'type': 'text', 'help': '^GSPC, ^DJI, AAPL…'},
                          {'key': 'name', 'label': 'Label', 'type': 'text'}]}]}
API = "https://query1.finance.yahoo.com/v8/finance/chart/{}?range=1d&interval=5m"


def fetch(ctx, opts):
    out = []
    for s in opts.get("symbols", []):
        try:
            d = ctx.http_json(API.format(urllib.parse.quote(s["sym"])), headers={"User-Agent": "Mozilla/5.0"})["chart"]["result"][0]
        except Exception:
            continue
        m = d["meta"]
        closes = [x for x in d["indicators"]["quote"][0].get("close", []) if x is not None]
        price, prev = m.get("regularMarketPrice"), m.get("chartPreviousClose") or m.get("previousClose")
        if price is None or not prev:
            continue
        step = max(1, len(closes) // 60)
        out.append({"name": s["name"], "price": price, "chg": price - prev, "pct": (price - prev) / prev * 100,
                    "prev": prev, "spark": [round(x, 2) for x in closes[::step]]})
    import time
    period = d["meta"].get("currentTradingPeriod", {}).get("regular", {}) if out else {}
    t = time.time()
    state = "open" if period and period["start"] <= t < period["end"] else "closed"
    return {"indices": out, "state": state} if out else None
