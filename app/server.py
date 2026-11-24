#!/usr/bin/env python3
"""ambient — Alexa-style idle screen for the Kiosk Satellite Echo Shows (Website screensaver mode).

Stdlib only. Runs from /app: this file + config.json, web shell in web/,
card plug-ins in /app/cards.

A card is a plug-in:  cards/<type>.py  (server: data)  +  cards/<type>.js  (browser: rendering)
                      + an entry in config.json "cards" (id, type, when, shows, duration, options).

  cards/<type>.py:  TTL = <seconds>            how long fetch() results are cached
                    def fetch(ctx, opts):       -> dict to render, or None to skip the card this time
  cards/<type>.js:  export function render(data, env) -> HTMLElement  (see web/app.js for env)

ctx (Ctx below) gives fetch() Home Assistant + Immich + plain HTTP helpers; keys never reach the browser.
Images from Immich go through /img/<asset-id> so the Shows never see the API key.

Admin (/admin, HTTP basic auth, password ADMIN_PASSWORD): views, per-card settings, integrations. Writable state
lives in DATA_DIR (a PVC), never in config.json (that is the shipped default):
  state.json    {"views": {id: {name, width, height, album, rotation, cards: {card id: bool}}},
                 "cards": {card id: {options, when, duration, every_minutes, repeat_minutes}},   # overrides
                 "location": {lat, lon}}
  secrets.json  {KEY: value}   integration endpoints + keys set in the admin (mode 0600); they win over the env
                (container environment), which stays the bootstrap/fallback. Secret values never reach a browser.
A card plug-in describes its settings form with META = {title, category, about, needs: [integration ids],
settings: [{key, label, type: text|number|bool|select|multi|tags|textarea|entity|album|list, help, choices,
domain (entity), fields + item (list; dotted keys reach nested dicts)}]}.
"""
import importlib.util
import json
import os
import re
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

APP = os.path.dirname(os.path.abspath(__file__))       # server.py + config.json
ROOT = os.environ.get("AMBIENT_ROOT", APP)              # holds web/, cards/, assets/ (siblings of core/ in k8s)
CARDS_DIR = os.path.join(ROOT, "cards")
sys.path.insert(0, CARDS_DIR)  # cards may import each other (mountain uses webcam.sun_elevation)
CONFIG = os.environ.get("AMBIENT_CONFIG", os.path.join(APP, "config.json"))
DATA = os.environ.get("DATA_DIR", "/data")
TZ = ZoneInfo(os.environ.get("TZ", "America/Los_Angeles"))
PORT = int(os.environ.get("PORT", "8099"))
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml",
         ".png": "image/png", ".webp": "image/webp"}


def log(*a):
    print(datetime.now(TZ).strftime("%H:%M:%S"), *a, flush=True)


# --- integrations: endpoints + keys. Value order: admin (secrets.json) > env (SOPS) > default.
INTEGRATIONS = [
    {"id": "ha", "name": "Home Assistant", "about": "States, history, calendars, weather, media players.",
     "fields": [{"key": "HA_URL", "label": "URL", "default": "http://homeassistant.local:8123", "placeholder": "http://homeassistant.local:8123"},
                {"key": "HA_TOKEN", "label": "Long-lived access token", "secret": True,
                 "help": "HA → your profile → Security → Long-lived access tokens"}]},
    {"id": "immich", "name": "Immich", "about": "Photo albums.",
     "fields": [{"key": "IMMICH_URL", "label": "URL", "placeholder": "http://192.168.1.20:2283"},
                {"key": "IMMICH_API_KEY", "label": "API key", "secret": True, "help": "Immich → Account settings → API keys"}]},
    {"id": "llm", "name": "LLM (OpenAI-compatible)", "about": "Zoltar, breaking-news judge, history picker, mountain vision.",
     "fields": [{"key": "LITELLM_URL", "label": "Base URL (…/v1)", "placeholder": "http://192.168.1.20:11434/v1 (Ollama) or https://openrouter.ai/api/v1"},
                {"key": "LITELLM_KEY", "label": "API key", "secret": True, "optional": True, "help": "Leave empty for a local Ollama"},
                {"key": "LLM_MODEL", "label": "Model (must accept images for the mountain card)", "placeholder": "gemma3:12b"}]},
    {"id": "tmdb", "name": "TMDb", "about": "New on streaming.",
     "fields": [{"key": "TMDB_TOKEN", "label": "API read access token", "secret": True,
                 "help": "themoviedb.org → Settings → API (the long 'read access token')"}]},
    {"id": "plex", "name": "Plex", "about": "Recently added.",
     "fields": [{"key": "PLEX_URL", "label": "Server URL", "placeholder": "http://192.168.1.20:32400"},
                {"key": "PLEX_TOKEN", "label": "Token", "secret": True, "help": "X-Plex-Token (support.plex.tv: finding an authentication token)"}]},
]
FIELDS = {f["key"]: f for i in INTEGRATIONS for f in i["fields"]}


SUPERVISOR = bool(os.environ.get("SUPERVISOR_TOKEN"))  # running as a Home Assistant app
INGRESS_PEER = "172.30.32.2"                           # HA's ingress proxy (the sidebar panel)


class Store:
    """Writable state (views, card overrides, location) and admin-set secrets, as JSON files in DATA."""

    def __init__(self):
        self.lock = threading.Lock()
        self.state_p, self.secret_p = os.path.join(DATA, "state.json"), os.path.join(DATA, "secrets.json")
        self.state, self.secrets = self._read(self.state_p), self._read(self.secret_p)
        self.mtime = time.time()

    @staticmethod
    def _read(p):
        try:
            with open(p) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            log(f"store: {p} unreadable ({e}); starting empty")
            return {}

    def _write(self, p, obj, mode=0o644):
        os.makedirs(DATA, exist_ok=True)
        tmp = p + ".tmp"
        with open(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode), "w") as f:
            json.dump(obj, f, indent=1, sort_keys=True)
        os.replace(tmp, p)
        self.mtime = time.time()

    def save_state(self, fn):
        with self.lock:
            fn(self.state)
            self._write(self.state_p, self.state)

    def save_secrets(self, fn):
        with self.lock:
            fn(self.secrets)
            self._write(self.secret_p, self.secrets, 0o600)

    def seed(self, cfg):
        """First boot: views from config.json "shows" (+ each card's "shows" list), home location."""
        if self.state.get("views") is not None:
            return
        photo = next((c for c in cfg["cards"] if c["type"] == "photo"), {})
        views = {}
        for sid, sv in cfg.get("shows", {}).items():
            views[sid] = {"name": sv.get("name", sid), "width": sv.get("width", 961), "height": sv.get("height", 601),
                          "album": photo.get("options", {}).get("album", ""),
                          "cards": {c["id"]: default_on(c, sid) for c in cfg["cards"]}}
        def f(st):
            st["views"] = views
            st.setdefault("cards", {})
            if cfg.get("location"):
                st.setdefault("location", cfg["location"])
        self.save_state(f)
        log("store: seeded views", ", ".join(views))

    def secret(self, key):
        v = self.secrets.get(key)
        if v:
            return v
        if SUPERVISOR and key in ("HA_URL", "HA_TOKEN"):  # an app reaches HA through the Supervisor proxy
            return "http://supervisor/core" if key == "HA_URL" else os.environ["SUPERVISOR_TOKEN"]
        return os.environ.get(key) or FIELDS.get(key, {}).get("default", "")

    def source(self, key):
        if self.secrets.get(key):
            return "admin"
        if SUPERVISOR and key in ("HA_URL", "HA_TOKEN"):
            return "app"
        return "env" if os.environ.get(key) else ""

    def ready(self, iid):
        integ = next((i for i in INTEGRATIONS if i["id"] == iid), None)
        return bool(integ) and all(self.secret(f["key"]) for f in integ["fields"] if not f.get("optional"))


def default_on(card, show):
    return card.get("enabled", True) is not False and (not card.get("shows") or show in card["shows"])


class Ctx:
    """What a card's fetch() gets. All calls are synchronous with short timeouts."""

    def __init__(self, store):
        self.store = store
        self.tz = TZ
        self._memo, self._lock = {}, threading.Lock()

    def secret(self, key):
        """An integration value (endpoint or key): admin-set, else env, else its default."""
        return self.store.secret(key)

    ha_token = property(lambda self: self.secret("HA_TOKEN"))
    ha_url = property(lambda self: self.secret("HA_URL").rstrip("/"))
    immich_key = property(lambda self: self.secret("IMMICH_API_KEY"))
    immich_url = property(lambda self: self.secret("IMMICH_URL").rstrip("/"))
    llm_key = property(lambda self: self.secret("LITELLM_KEY"))

    # --- time
    def now(self):
        return datetime.now(TZ)

    # --- generic
    def http_json(self, url, body=None, headers=None, timeout=12):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Accept": "application/json", "User-Agent": "ambient/1"}
        if data is not None:
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
            return json.load(r)

    def memo(self, key, ttl, fn):
        """Cache any helper result for ttl seconds (shared by all cards)."""
        with self._lock:
            hit = self._memo.get(key)
            if hit and hit[0] > time.time():
                return hit[1]
        val = fn()
        with self._lock:
            self._memo[key] = (time.time() + ttl, val)
        return val

    # --- Home Assistant
    def ha(self, path, body=None):
        return self.http_json(self.ha_url + "/api/" + path.lstrip("/"), body, {"Authorization": "Bearer " + self.ha_token})

    def state(self, entity_id):
        """State object {state, attributes, last_changed...} or None if missing."""
        try:
            return self.ha("states/" + entity_id)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def history(self, entity_id, hours):
        start = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        q = urllib.parse.urlencode({"filter_entity_id": entity_id, "minimal_response": "", "no_attributes": ""})
        res = self.ha(f"history/period/{start}?{q}")
        return res[0] if res else []

    def service(self, domain, service, data, response=False):
        return self.ha(f"services/{domain}/{service}" + ("?return_response" if response else ""), data)

    # --- Immich
    def immich(self, path, body=None):
        return self.http_json(self.immich_url + "/api/" + path.lstrip("/"), body, {"x-api-key": self.immich_key})

    # --- LLM (LiteLLM, key "ambient": free models only)
    def llm(self, prompt, model=None, max_tokens=400, image_url=None, temperature=0.9):
        content = prompt if not image_url else [{"type": "text", "text": prompt},
                                                {"type": "image_url", "image_url": {"url": image_url}}]
        r = self.http_json(self.secret("LITELLM_URL").rstrip("/") + "/chat/completions",
                           {"model": model or self.secret("LLM_MODEL"), "messages": [{"role": "user", "content": content}],
                            "max_tokens": max_tokens, "temperature": temperature},
                           {"Authorization": "Bearer " + self.llm_key}, timeout=90)
        return (r["choices"][0]["message"].get("content") or "").strip()

    @staticmethod
    def img(asset_id):
        """Browser URL for an Immich asset preview (proxied, key stays here)."""
        return f"img/{asset_id}"


class Cards:
    """Loads card plug-ins and caches their fetch() results per (card id, show)."""

    def __init__(self, ctx):
        self.ctx, self.mods, self.cache, self.locks = ctx, {}, {}, {}
        self.guard = threading.Lock()
        self.load()

    def load(self):
        for f in sorted(os.listdir(CARDS_DIR)):
            if f.endswith(".py") and not f.startswith("_"):
                name = f[:-3]
                try:
                    spec = importlib.util.spec_from_file_location("card_" + name, os.path.join(CARDS_DIR, f))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self.mods[name] = mod
                except Exception:
                    log("card plug-in failed to load:", name)
                    traceback.print_exc()
        log("cards:", ", ".join(sorted(self.mods)))

    def get(self, card, show):
        mod = self.mods.get(card["type"])
        if not mod:
            return None
        key = (card["id"], show)
        with self.guard:
            lock = self.locks.setdefault(key, threading.Lock())
        with lock:  # one fetch per card at a time; others wait for the result
            hit = self.cache.get(key)
            if hit and hit[0] > time.time():
                return hit[1]
            try:
                opts = dict(card.get("options", {}), _show=show, _card=card["id"])
                data = mod.fetch(self.ctx, opts)
                ttl = getattr(mod, "TTL", 60)
            except Exception as e:
                log(f"card {card['id']} failed: {type(e).__name__}: {e}")
                data = hit[1] if hit else None  # keep the last good data through a blip
                ttl = 30
            self.cache[key] = (time.time() + ttl, data)
            return data


def _get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ambient)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(), r.headers.get("Content-Type", "image/jpeg")


def in_window(when, now):
    """when: {"days": "mon-fri" | ["sat","sun"], "hours": ["05:30-10:00", ...]} — all optional."""
    if not when:
        return True
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    d = when.get("days")
    if d:
        if isinstance(d, str) and "-" in d:
            a, b = d.split("-")
            ok = days[days.index(a):days.index(b) + 1]
        else:
            ok = d if isinstance(d, list) else [d]
        if days[now.weekday()] not in ok:
            return False
    hrs = when.get("hours")
    if hrs:
        hm = now.strftime("%H:%M")
        if not any(a <= hm < b for a, b in (h.split("-") for h in hrs)):
            return False
    return True


def base_config():
    with open(CONFIG) as f:
        return json.load(f)


OVERRIDABLE = ("when", "duration", "every_minutes", "repeat_minutes")


def card_name(c):
    mod = CARDS.mods.get(c["type"])
    return c.get("name") or getattr(mod, "META", {}).get("title") or c["id"]


def load_config():
    """config.json (shipped defaults) with the admin's card overrides applied, and the views."""
    cfg = base_config()
    st = STORE.state
    loc = st.get("location") or ha_location()
    cards = []
    for c in cfg["cards"]:
        c = dict(c)
        ov = st.get("cards", {}).get(c["id"], {})
        opts = dict(c.get("options", {}), **ov.get("options", {}))
        for k in ("lat", "lon"):  # cards that take a location default to home
            if opts.get(k) in (None, "") and loc.get(k) not in (None, ""):
                opts[k] = loc[k]
        c["options"] = opts
        for k in OVERRIDABLE:
            if k in ov:
                c[k] = ov[k]
        cards.append(c)
    cfg["cards"] = cards
    cfg["views"] = st.get("views") or {}
    return cfg


def ha_location():
    """Home location from Home Assistant's config, rounded to 2 decimals, when none is set in the admin."""
    if not STORE.ready("ha"):
        return {}
    def get():
        try:
            c = CTX.ha("config")
            return {"lat": round(c["latitude"], 2), "lon": round(c["longitude"], 2)}
        except Exception:
            return {}
    return CTX.memo(("ha-location",), 3600, get)


def view_card(cfg, card, show):
    """The card as this view runs it (photo album per view), or None if the view has it switched off."""
    view = cfg["views"].get(show)
    if view is not None:
        on = view.get("cards", {}).get(card["id"])
        if on is None:
            on = default_on(card, show)
        if not on:
            return None
        if card["type"] == "photo" and view.get("album"):
            card = dict(card, options=dict(card["options"], album=view["album"]))
    elif not default_on(card, show):
        return None
    return card


def needs_ready(card):
    return all(STORE.ready(n) for n in getattr(CARDS.mods.get(card["type"]), "META", {}).get("needs", []))


def cards_for(cfg, show, now, preview=False):
    out = []
    for c in cfg["cards"]:
        if not needs_ready(c):  # e.g. no TMDb token: the streaming cards just stay out of the rotation
            continue
        if not preview and cfg["views"].get(show, {}).get("lite") and getattr(CARDS.mods.get(c["type"]), "META", {}).get("heavy"):
            continue  # low-power screen: no live video
        c = view_card(cfg, c, show) if not preview else c
        if c and (preview or in_window(c.get("when"), now)):
            out.append(c)
    return out


def _version():
    """Hash of the shipped code, so open pages reload themselves after a deploy."""
    import hashlib
    h = hashlib.sha1()
    for d in (APP, os.path.join(ROOT, "web"), os.path.join(ROOT, "assets"), os.path.join(ROOT, "vendor"), CARDS_DIR):
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            fp = os.path.join(d, f)
            if os.path.isfile(fp):
                with open(fp, "rb") as fh:
                    h.update(f.encode() + fh.read())
    return h.hexdigest()[:10]


VERSION = _version()
STORE = Store()
CTX = Ctx(STORE)
CARDS = Cards(CTX)
WEB = os.path.join(ROOT, "web")
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


# --- admin -------------------------------------------------------------------------------------------------
def _hint(v):
    return ("…" + v[-4:]) if v and len(v) > 8 else ("set" if v else "")


def admin_state(handler=None):
    cfg = load_config()
    base = {c["id"]: c for c in base_config()["cards"]}
    cards = []
    for c in cfg["cards"]:
        meta = getattr(CARDS.mods.get(c["type"]), "META", {})
        ov = STORE.state.get("cards", {}).get(c["id"], {})
        cards.append({"id": c["id"], "type": c["type"], "name": card_name(c), "category": meta.get("category", "Other"),
                      "about": meta.get("about", ""), "needs": meta.get("needs", []), "settings": meta.get("settings", []),
                      "options": c["options"], "defaults": base[c["id"]].get("options", {}),
                      "interrupt": bool(c.get("interrupt")), "layer": c.get("layer"), "heavy": bool(meta.get("heavy")),
                      "schedule": {k: c.get(k) for k in OVERRIDABLE}, "overridden": bool(ov),
                      "default_shows": base[c["id"]].get("shows"), "default_enabled": base[c["id"]].get("enabled", True) is not False})
    integ = []
    for i in INTEGRATIONS:
        fields = []
        for f in i["fields"]:
            v = STORE.secret(f["key"])
            fields.append(dict(f, value=None if f.get("secret") else v, set=bool(v),
                               hint=_hint(v) if f.get("secret") else None, source=STORE.source(f["key"])))
        integ.append(dict(i, fields=fields, ready=STORE.ready(i["id"])))
    return {"views": cfg["views"], "cards": cards, "integrations": integ, "rotation": cfg.get("rotation", {}),
            "location": STORE.state.get("location", {}), "version": VERSION,
            "password_set": bool(STORE.secret("ADMIN_PASSWORD")), "app": SUPERVISOR,
            "ingress": bool(handler and handler.ingress()), "screen_base": handler.screen_base() if handler else "",
            "location_from_ha": not STORE.state.get("location") and bool(ha_location())}


def test_integration(iid):
    c = CTX
    if iid == "ha":
        r = c.ha("")
        return r.get("message", "ok")
    if iid == "immich":
        r = c.immich("server/about")
        return "Immich " + str(r.get("version", "ok"))
    if iid == "llm":
        r = c.http_json(c.secret("LITELLM_URL").rstrip("/") + "/models", headers={"Authorization": "Bearer " + c.llm_key})
        ids = [m.get("id") for m in r.get("data", [])]
        model = c.secret("LLM_MODEL")
        return f"{len(ids)} models" + ("" if not model or model in ids else f" — '{model}' is not one of them")
    if iid == "tmdb":
        c.http_json("https://api.themoviedb.org/3/configuration", headers={"Authorization": "Bearer " + c.secret("TMDB_TOKEN")})
        return "token accepted"
    if iid == "plex":
        req = urllib.request.Request(c.secret("PLEX_URL").rstrip("/") + "/library/sections",
                                     headers={"X-Plex-Token": c.secret("PLEX_TOKEN"), "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            n = len(json.load(r).get("MediaContainer", {}).get("Directory", []))
        return f"{n} libraries"
    raise ValueError("unknown integration")


def clean_view(v):
    out = {"name": str(v.get("name") or "View")[:60],
           "width": max(200, min(4000, int(v.get("width") or 961))), "height": max(150, min(4000, int(v.get("height") or 601))),
           "album": str(v.get("album") or "") if UUID.match(str(v.get("album") or "")) else "",
           "cards": {str(k): bool(x) for k, x in (v.get("cards") or {}).items()}}
    if v.get("lite"):
        out["lite"] = True
    rot = {k: int(x) for k, x in (v.get("rotation") or {}).items()
           if k in ("photos_between", "photo_seconds", "card_seconds") and x not in (None, "")}
    if rot:
        out["rotation"] = rot
    return out


def app_host_port():
    """The host port the user mapped to the screens' port in the app's Network settings (Supervisor API)."""
    def get():
        try:
            r = CTX.http_json("http://supervisor/addons/self/info", headers={"Authorization": "Bearer " + os.environ["SUPERVISOR_TOKEN"]})
            return (r.get("data", {}).get("network") or {}).get(f"{PORT}/tcp")
        except Exception:
            return None
    return CTX.memo(("app-port",), 300, get)


class Handler(BaseHTTPRequestHandler):
    server_version = "ambient/1"

    def log_message(self, fmt, *args):  # quiet: only errors are logged
        pass

    def send(self, code, body, ctype="application/json", cache="no-store", headers=None):
        if isinstance(body, (dict, list)) or body is None:
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def file(self, path):
        ext = os.path.splitext(path)[1]
        if not os.path.isfile(path) or ext not in TYPES:
            return self.send(404, {"error": "not found"})
        with open(path, "rb") as f:
            self.send(200, f.read(), TYPES[ext], "no-cache")

    # --- admin auth: HTTP basic, any user name, password ADMIN_PASSWORD (admin-set or env). None set = open.
    def ingress(self):
        return SUPERVISOR and self.client_address[0] == INGRESS_PEER and bool(self.headers.get("X-Ingress-Path"))

    def screen_base(self):
        """Where kiosks point: this host on the screens' port (under ingress the Host header is HA's)."""
        host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "localhost").split(",")[0].strip()
        name = host.rsplit(":", 1)[0] if not host.endswith("]") else host
        port = os.environ.get("SCREEN_PORT") or (app_host_port() if SUPERVISOR else None) or PORT
        return f"http://{name}:{port}/"

    def authed(self):
        if self.ingress():  # HA already signed the user in (admin users only: panel_admin)
            return True
        pw = STORE.secret("ADMIN_PASSWORD")
        if not pw:
            if SUPERVISOR:  # an app without a password: admin only from the HA sidebar
                self.send(403, "Open ambient from the Home Assistant sidebar, or set an admin password there.", "text/plain; charset=utf-8")
                return False
            return True
        import base64
        import hmac
        h = self.headers.get("Authorization", "")
        if h.startswith("Basic "):
            try:
                given = base64.b64decode(h[6:]).decode().split(":", 1)[1]
                if hmac.compare_digest(given.encode(), pw.encode()):
                    return True
            except Exception:
                pass
        self.send(401, {"error": "auth"}, headers={"WWW-Authenticate": 'Basic realm="ambient admin"'})
        return False

    def body(self):
        if "application/json" not in self.headers.get("Content-Type", ""):  # blocks cross-site form posts
            raise ValueError("JSON only")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1_000_000:
            raise ValueError("too big")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_PUT(self):
        self.write("PUT")

    def do_POST(self):
        self.write("POST")

    def do_DELETE(self):
        self.write("DELETE")

    def write(self, verb):
        p = urllib.parse.urlsplit(self.path).path
        try:
            if not p.startswith("/api/admin/") or not self.authed():
                return None if p.startswith("/api/admin/") else self.send(404, {"error": "not found"})
            data = self.body() if verb != "DELETE" else {}
            m = re.match(r"^/api/admin/views/([a-z0-9_-]+)$", p)
            if m:
                vid = m.group(1)
                if not SLUG.match(vid):
                    return self.send(400, {"error": "view id: lowercase letters, digits, - and _"})
                if verb == "DELETE":
                    STORE.save_state(lambda st: st.get("views", {}).pop(vid, None))
                else:
                    v = clean_view(data)
                    STORE.save_state(lambda st: st.setdefault("views", {}).__setitem__(vid, v))
                CARDS.cache.clear()
                return self.send(200, admin_state(self))
            m = re.match(r"^/api/admin/cards/([a-z0-9_-]+)$", p)
            if m:
                cid = m.group(1)
                if not any(c["id"] == cid for c in base_config()["cards"]):
                    return self.send(404, {"error": "no such card"})
                if verb == "DELETE":  # back to the shipped defaults
                    STORE.save_state(lambda st: st.get("cards", {}).pop(cid, None))
                else:
                    ov = {"options": {k: v for k, v in (data.get("options") or {}).items() if not k.startswith("_")}}
                    for k in OVERRIDABLE:
                        if k in (data.get("schedule") or {}):
                            ov[k] = data["schedule"][k]
                    STORE.save_state(lambda st: st.setdefault("cards", {}).__setitem__(cid, ov))
                CARDS.cache.clear()
                return self.send(200, admin_state(self))
            if p == "/api/admin/location" and verb == "PUT":
                loc = {k: float(data[k]) for k in ("lat", "lon") if data.get(k) not in (None, "")}
                STORE.save_state(lambda st: st.__setitem__("location", loc))
                CARDS.cache.clear()
                return self.send(200, admin_state(self))
            m = re.match(r"^/api/admin/integrations/([a-z]+)(/test)?$", p)
            if m:
                integ = next((i for i in INTEGRATIONS if i["id"] == m.group(1)), None)
                if not integ:
                    return self.send(404, {"error": "no such integration"})
                if m.group(2):
                    try:
                        return self.send(200, {"ok": True, "detail": test_integration(integ["id"])})
                    except urllib.error.HTTPError as e:
                        return self.send(200, {"ok": False, "detail": f"HTTP {e.code} {e.reason}"})
                    except Exception as e:
                        return self.send(200, {"ok": False, "detail": f"{type(e).__name__}: {e}"[:200]})
                keys = {f["key"] for f in integ["fields"]}

                def f(sec):
                    for k, v in (data.get("values") or {}).items():
                        if k in keys and isinstance(v, str) and v.strip():
                            sec[k] = v.strip()
                    for k in data.get("clear") or []:
                        if k in keys:
                            sec.pop(k, None)
                STORE.save_secrets(f)
                CTX._memo.clear()
                CARDS.cache.clear()
                return self.send(200, admin_state(self))
            if p == "/api/admin/password" and verb == "PUT":
                pw = str(data.get("password") or "")
                if len(pw) < 8:
                    return self.send(400, {"error": "at least 8 characters"})
                STORE.save_secrets(lambda sec: sec.__setitem__("ADMIN_PASSWORD", pw))
                return self.send(200, {"ok": True})
            return self.send(404, {"error": "not found"})
        except BrokenPipeError:
            pass
        except Exception as e:
            log(f"{verb} {p} failed: {type(e).__name__}: {e}")
            try:
                self.send(400, {"error": f"{type(e).__name__}: {e}"[:200]})
            except Exception:
                pass

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        show = re.sub(r"[^a-z0-9_-]", "", q.get("show", "default").lower())[:32] or "default"
        p = u.path
        try:
            if p in ("/", "/index.html"):
                return self.file(os.path.join(WEB, "index.html"))
            if p in ("/app.js", "/style.css"):
                return self.file(os.path.join(WEB, p[1:]))
            if p in ("/admin", "/admin/", "/admin.js", "/admin.css"):
                if not self.authed():
                    return None
                return self.file(os.path.join(WEB, "admin.html" if p.startswith("/admin/") or p == "/admin" else p[1:]))
            if p.startswith("/api/admin/"):
                if not self.authed():
                    return None
                if p == "/api/admin/state":
                    return self.send(200, admin_state(self))
                if p == "/api/admin/albums":
                    if not STORE.ready("immich"):
                        return self.send(400, {"error": "set up Immich under Integrations"})
                    al = CTX.immich("albums") + CTX.immich("albums?shared=true")
                    seen, out = set(), []
                    for a in al:
                        if a["id"] not in seen:
                            seen.add(a["id"])
                            out.append({"id": a["id"], "name": a.get("albumName", ""), "count": a.get("assetCount", 0)})
                    return self.send(200, sorted(out, key=lambda a: a["name"].lower()))
                if p == "/api/admin/entities":
                    if not STORE.ready("ha"):
                        return self.send(400, {"error": "Home Assistant isn't connected"})
                    dom = re.sub(r"[^a-z_]", "", q.get("domain", ""))
                    sts = CTX.memo(("admin-states",), 60, lambda: CTX.ha("states"))
                    return self.send(200, sorted(({"id": s["entity_id"], "name": s["attributes"].get("friendly_name", "")}
                                                  for s in sts if not dom or s["entity_id"].startswith(dom + ".")),
                                                 key=lambda e: e["id"]))
                return self.send(404, {"error": "not found"})
            m = re.match(r"^/vendor/([a-z0-9_.-]+\.js)$", p)
            if m and ".." not in m.group(1):
                return self.file(os.path.join(ROOT, "vendor", m.group(1)))
            m = re.match(r"^/assets/([a-z0-9_-]+\.(png|svg|webp))$", p)
            if m:
                return self.file(os.path.join(ROOT, "assets", m.group(1)))
            m = re.match(r"^/cards/([a-z0-9_]+)\.js$", p)
            if m:
                return self.file(os.path.join(CARDS_DIR, m.group(1) + ".js"))
            if p == "/healthz":
                return self.send(200, {"ok": True, "cards": sorted(CARDS.mods)})
            if p == "/api/config":
                cfg = load_config()
                now = CTX.now()
                view = cfg["views"].get(show) or cfg.get("shows", {}).get(show, {})
                return self.send(200, {
                    "show": show, "showName": view.get("name", show),
                    "rotation": dict(cfg.get("rotation", {}), **view.get("rotation", {})),
                    "lite": bool(view.get("lite")),
                    "cards": [{k: c.get(k) for k in ("id", "type", "duration", "interrupt", "overlay", "repeat_minutes", "every_minutes", "layer")}
                              for c in cards_for(cfg, show, now)],
                    # code hash + admin edits: open pages reload when either changes
                    "version": VERSION + "-" + str(int(STORE.mtime)),
                })
            m = re.match(r"^/api/card/([a-z0-9_-]+)$", p)
            if m:
                cfg = load_config()
                card = next((c for c in cfg["cards"] if c["id"] == m.group(1)), None)
                if card and q.get("preview"):
                    card = view_card(cfg, card, show) or card  # preview: ignore the time window and the view's switch
                elif card:
                    card = next((c for c in cards_for(cfg, show, CTX.now()) if c["id"] == card["id"]), None)
                if not card:
                    return self.send(200, {"data": None, "reason": "not active"})
                return self.send(200, {"data": CARDS.get(card, show)})
            m = re.match(r"^/x/([a-z0-9_-]+)/([a-z0-9_-]{1,40})$", p)
            if m:  # per-card asset proxy: the card's asset(ctx, opts, key) returns (bytes, content type)
                card = next((c for c in load_config()["cards"] if c["id"] == m.group(1)), None)
                mod = card and CARDS.mods.get(card["type"])
                if mod and hasattr(mod, "asset"):
                    data, ctype = mod.asset(CTX, dict(card.get("options", {}), _card=card["id"]), m.group(2))
                    return self.send(200, data, ctype, "public, max-age=300")
                return self.send(404, {"error": "no asset"})
            m = re.match(r"^/cam/([a-z0-9_-]+)$", p)
            if m:  # webcam image proxy: the card plug-in says where the cam's current image is
                cfg = load_config()
                for c in cfg["cards"]:
                    cam = next((x for x in c.get("options", {}).get("cams", []) if x["id"] == m.group(1)), None)
                    mod = CARDS.mods.get(c["type"])
                    if cam and mod and hasattr(mod, "cam_image"):
                        data, ctype = mod.cam_image(CTX, cam)
                        return self.send(200, data, ctype, "public, max-age=30")
                return self.send(404, {"error": "no such cam"})
            m = re.match(r"^/img/([0-9a-f-]{36})$", p)
            if m and UUID.match(m.group(1)):
                size = "fullsize" if q.get("size") == "full" else "preview"
                req = urllib.request.Request(f"{CTX.immich_url}/api/assets/{m.group(1)}/thumbnail?size={size}",
                                             headers={"x-api-key": CTX.immich_key})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return self.send(200, r.read(), r.headers.get("Content-Type", "image/jpeg"),
                                     "public, max-age=86400")
            return self.send(404, {"error": "not found"})
        except BrokenPipeError:
            pass
        except Exception as e:
            log(f"GET {p} failed: {type(e).__name__}: {e}")
            try:
                self.send(502, {"error": type(e).__name__})
            except Exception:
                pass


if __name__ == "__main__":
    STORE.seed(base_config())
    if not CTX.ha_token or not CTX.immich_key:
        log("WARNING: HA_TOKEN / IMMICH_API_KEY not set (env or admin → Integrations)")
    if not STORE.secret("ADMIN_PASSWORD"):
        log("WARNING: ADMIN_PASSWORD not set: /admin is open to anyone who can reach this port")
    log(f"ambient listening on :{PORT}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
