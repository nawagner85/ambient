// ambient — rotation engine. Cards are plug-ins: /cards/<type>.js exports render(data, env) -> HTMLElement.
// Rotation: `photos_between` photo slides, then the next info card that has something to show (round robin).
// Interrupt cards (planes) are polled and cut in as soon as they have data.
const params = new URLSearchParams(location.search);
const show = params.get('show') || 'default';
const only = params.get('card');  // preview: ?card=<id> pins one card (ignores its time window)
const stage = document.getElementById('stage');
const corner = document.getElementById('corner');
const mods = {};
let cfg = null, deck = [], infoIdx = 0, sinceInfo = 0, timer = null, pending = null, busy = false;
const seen = {};  // interrupt card id -> {key: last shown ms}
const lastShown = {};  // card id -> ms (for every_minutes)

const ICONS = {
  'clear-night': '🌙', cloudy: '☁️', exceptional: '⚠️', fog: '🌫️', hail: '🌨️', lightning: '⛈️',
  'lightning-rainy': '⛈️', partlycloudy: '⛅', pouring: '🌧️', rainy: '🌦️', snowy: '❄️',
  'snowy-rainy': '🌨️', sunny: '☀️', windy: '💨', 'windy-variant': '💨',
};

// Helpers handed to every card renderer.
const env = {
  show,
  icon: (cond) => ICONS[cond] || '🌡️',
  label: (cond) => (cond || '').replace('partlycloudy', 'partly cloudy').replace('clear-night', 'clear')
    .replace(/-/g, ' ').replace(/^./, (c) => c.toUpperCase()),
  // h('div.class.other', {attr: v}, child, 'text', ...)
  h(tag, attrs, ...kids) {
    const [name, ...cls] = tag.split('.');
    const el = document.createElement(name || 'div');
    if (cls.length) el.className = cls.join(' ');
    if (attrs && (attrs.constructor === Object)) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v == null || v === false) continue;
        if (k === 'style' && typeof v === 'object') {
          for (const [sk, sv] of Object.entries(v)) sk.startsWith('--') ? el.style.setProperty(sk, sv) : (el.style[sk] = sv);
        }
        else el.setAttribute(k, v);
      }
    } else if (attrs != null) kids.unshift(attrs);
    for (const k of kids.flat()) if (k != null && k !== false) el.append(k instanceof Node ? k : String(k));
    return el;
  },
  time: (d = new Date()) => d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
  day: (iso) => new Date(iso).toLocaleDateString('en-US', { weekday: 'short' }),
};

async function api(path) {
  const r = await fetch(path + (path.includes('?') ? '&' : '?') + 'show=' + encodeURIComponent(show), { cache: 'no-store' });
  if (!r.ok) throw new Error(path + ' ' + r.status);
  return r.json();
}

async function loadConfig() {
  const c = await api('api/config');
  if (cfg && c.version !== cfg.version) location.reload();  // new deploy: pick up new code
  env.lite = !!c.lite;
  for (const card of c.cards) {
    if (!mods[card.type]) {
      try { mods[card.type] = await import(`cards/${card.type}.js?v=${c.version}`); }
      catch (e) { console.warn('renderer failed', card.type, e); }
    }
  }
  cfg = c;
}

const R = () => Object.assign({ photos_between: 4, photo_seconds: 10, card_seconds: 15, interrupt_poll_seconds: 15 }, cfg.rotation);
const cardsOf = (pred) => cfg.cards.filter((c) => mods[c.type] && pred(c));

// YouTube embeds (enablejsapi=1): resolve when the player reports state 1 (playing).
function ytPlaying(f) {
  return new Promise((ok) => {
    if (f.dataset.playing) return ok();
    const onMsg = (e) => {
      if (e.source !== f.contentWindow) return;
      let m; try { m = typeof e.data === 'string' ? JSON.parse(e.data) : e.data; } catch { return; }
      const st = m && (m.info && m.info.playerState !== undefined ? m.info.playerState : m.event === 'onStateChange' ? m.info : undefined);
      if (st === 1) { f.dataset.playing = 1; window.removeEventListener('message', onMsg); ok(); }
    };
    window.addEventListener('message', onMsg);
    const hello = () => { try { f.contentWindow.postMessage(JSON.stringify({ event: 'listening', id: 1, channel: 'widget' }), '*'); } catch {} };
    f.addEventListener('load', () => { hello(); setTimeout(hello, 1000); setTimeout(hello, 3000); }, { once: true });
  });
}

// Wait until a slide's media is ready: images loaded, iframes loaded (+1.5 s for the player to start),
// videos playing. Never longer than ms.
function waitImages(el, ms = 8000) {
  const imgs = [...el.querySelectorAll('img')];
  const frames = [...el.querySelectorAll('iframe')];
  const vids = [...el.querySelectorAll('video')];
  return Promise.race([
    Promise.all([
      ...imgs.map((i) => (i.complete ? null : new Promise((ok) => { i.onload = ok; i.onerror = ok; }))),
      ...frames.map((f) => ytPlaying(f)),
      ...vids.map((v) => new Promise((ok) => { v.addEventListener('playing', ok, { once: true }); v.addEventListener('error', ok, { once: true }); })),
    ]),
    new Promise((ok) => setTimeout(ok, ms)),
  ]);
}

let z = 1, preloaded = null;  // preloaded: {card, data, el, ready, at}

function build(card, data) {
  const el = env.h('div.slide.card-' + card.type);
  el.append(mods[card.type].render(data, env));
  return el;
}

// Build the next info card now, invisible and underneath, so iframes/videos load and start playing.
// Never moved in the DOM afterwards (moving an iframe reloads it); it is revealed by z-index + opacity.
async function preloadNext() {
  if (preloaded || only) return;
  const pick = await nextInfo();
  if (!pick) return;
  const el = build(...pick);
  el.classList.add('pre');
  el.style.zIndex = 0;
  stage.append(el);
  preloaded = { card: pick[0], data: pick[1], el, ready: waitImages(el, 15000), at: Date.now() };
}

async function present(card, data, el) {
  el = el || build(card, data);
  if (!el.isConnected) stage.append(el);
  el.style.zIndex = ++z;
  el.classList.remove('pre');
  await waitImages(el);
  requestAnimationFrame(() => el.classList.add('in'));
  lastShown[card.id] = Date.now();
  // layer 'over': play on top of what is showing (Emi's screen clean); otherwise replace it
  for (const old of [...stage.children]) {
    if (old === el || old.classList.contains('pre') || (card.layer === 'over' && !old.classList.contains('over'))) continue;
    old.classList.remove('in'); setTimeout(() => old.remove(), 1500);
  }
  if (card.layer === 'over') el.classList.add('over');
  corner.hidden = card.overlay !== 'corner';
  // a renderer can ask for more time (data-seconds on its root, e.g. Zoltar's typing); never less than configured
  const want = Number((el.firstElementChild && el.firstElementChild.dataset.seconds) || 0);
  const sec = Math.max(want, card.duration || (card.type === 'photo' ? R().photo_seconds : R().card_seconds));
  return sec * 1000;
}

async function nextInfo() {
  const info = cardsOf((c) => c.type !== 'photo' && !c.interrupt);
  for (let i = 0; i < info.length; i++) {
    const card = info[(infoIdx + i) % info.length];
    if (card.every_minutes && Date.now() - (lastShown[card.id] || 0) < card.every_minutes * 60000) continue;
    try {
      const { data } = await api('api/card/' + card.id);
      if (data) { infoIdx = (infoIdx + i + 1) % info.length; return [card, data]; }
    } catch (e) { console.warn(card.id, e); }
  }
  return null;
}

async function nextPhoto() {
  const card = cardsOf((c) => c.type === 'photo')[0];
  if (!card) return null;
  if (!deck.length) {
    const { data } = await api('api/card/' + card.id);
    deck = (data && data.slides) || [];
  }
  const slide = deck.shift();
  return slide ? [card, slide] : null;
}

async function advance() {
  if (busy) return;
  busy = true;
  clearTimeout(timer);
  let wait = 5000;
  try {
    let pick = null;
    if (only) {
      const card = cfg.cards.find((c) => c.id === only) || { id: only, type: only };
      if (!mods[card.type]) mods[card.type] = await import(`cards/${card.type}.js?v=${cfg.version}`);
      const { data } = await api('api/card/' + only + '?preview=1');
      pick = card.type === 'photo' ? [card, data.slides[0]] : data ? [card, data] : null;
    }
    if (!pick && pending) { pick = pending; pending = null; }
    if (!pick && sinceInfo >= R().photos_between) {
      if (preloaded && Date.now() - preloaded.at < 90000) {
        const p = preloaded; preloaded = null;
        await p.ready;                       // usually done already: it buffered during the last photo
        pick = [p.card, p.data, p.el];
      } else {
        if (preloaded) { preloaded.el.remove(); preloaded = null; }
        pick = await nextInfo();
      }
      sinceInfo = 0;
    }
    if (!pick) { pick = await nextPhoto(); if (pick) sinceInfo++; }
    if (!pick) pick = await nextInfo();
    if (pick) wait = await present(...pick);
    // the next slide will be an info card: start loading it now, hidden
    if (!only && sinceInfo >= R().photos_between && !preloaded) setTimeout(() => preloadNext().catch(() => {}), 500);
  } catch (e) { console.warn('advance', e); }
  busy = false;
  timer = setTimeout(advance, wait);
}

async function pollInterrupts() {
  if (!cfg) return;
  for (const card of cardsOf((c) => c.interrupt)) {
    try {
      const { data } = await api('api/card/' + card.id);
      if (!data) continue;
      const key = data.hex || data.id || JSON.stringify(data);
      const s = (seen[card.id] = seen[card.id] || {});
      const repeat = (card.repeat_minutes || 10) * 60000;
      if (s[key] && Date.now() - s[key] < repeat) continue;
      s[key] = Date.now();
      pending = [card, data];
      advance();  // cut in now
      return;
    } catch (e) { console.warn(card.id, e); }
  }
}

async function tickCorner() {
  document.getElementById('corner-time').textContent = env.time();
  try {
    const { data } = await api('api/card/weather');
    document.getElementById('corner-weather').textContent = data ? `${env.icon(data.cond)} ${Math.round(data.temp)}°` : '';
  } catch (e) { /* keep last */ }
}

async function boot() {
  for (;;) {
    try { await loadConfig(); break; } catch (e) { await new Promise((ok) => setTimeout(ok, 5000)); }
  }
  setInterval(() => loadConfig().catch(() => {}), 60000);  // picks up deploys and admin edits
  setInterval(pollInterrupts, R().interrupt_poll_seconds * 1000);
  setInterval(tickCorner, 30000);
  setTimeout(() => location.reload(), (cfg.lite ? 2 : 6) * 3600000);  // WebView hygiene (sooner on low-power screens)
  tickCorner();
  advance();
}
boot();
