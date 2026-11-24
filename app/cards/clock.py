"""Fun clocks (Chumby tribute): the browser draws them; this only says which styles are on.
options: styles: ["domo", "space", "robo"] (rotates one per appearance)."""
TTL = 3600
# admin page: title, category, required integrations, settings form (server.py SETTINGS doc)
META = {'title': 'Fun clocks',
 'category': 'Fun',
 'about': 'Chumby-style animated clocks, one style per appearance.',
 'settings': [{'key': 'styles',
               'label': 'Styles (in turn)',
               'type': 'tags',
               'choices': ['isle', 'domo', 'flip', 'space', 'robo']}]}


def fetch(ctx, opts):
    return {"styles": opts.get("styles", ["domo", "space", "robo"])}
