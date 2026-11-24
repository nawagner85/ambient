"""Screen Clean, Emi edition (Chumby's 'Screen Clean' dog tribute): plays on top of the current photo
(config layer: "over"). No data needed; options: caption."""
TTL = 3600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Screen clean',
 'category': 'Fun',
 'about': 'Emi licks the glass, then a squeegee wipes it.',
 'settings': [{'key': 'caption', 'label': 'Caption', 'type': 'text'}]}


def fetch(ctx, opts):
    return {"emi": "assets/emi.png", "caption": opts.get("caption", "Screen cleaned by Emi")}
