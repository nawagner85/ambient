"""The Secret Life of Emi: today's episode only (a HA sensor whose entity_picture is today's image; off by default). options: entity."""
import re

TTL = 300
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Daily episode (Emi)',
 'category': 'Home',
 'needs': ['ha'],
 'about': "Today's episode image from a HA sensor.",
 'settings': [{'key': 'entity', 'label': 'Episode sensor', 'type': 'entity', 'domain': 'sensor'}]}


def fetch(ctx, opts):
    s = ctx.state(opts.get("entity", "sensor.emi_episode"))
    if not s or s["state"] != ctx.now().date().isoformat():
        return None
    a = s["attributes"]
    m = re.search(r"/assets/([0-9a-f-]{36})/", a.get("image_url") or "")
    if not m:
        return None
    return {"img": ctx.img(m.group(1)), "caption": a.get("caption", ""), "date": s["state"]}
