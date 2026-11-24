// ambient admin: views (size, album, which cards), card settings (forms from each card plug-in's META),
// integrations (endpoints + keys; secret values are write-only here, the server never sends them back).
const $ = (s, el = document) => el.querySelector(s);
const main = $('#main'), drawer = $('#drawer');
let S = null, tab = 'views', cur = null, draft = null, albums = null;
const ents = {};

function h(tag, attrs, ...kids) {
  const [name, ...cls] = tag.split('.');
  const el = document.createElement(name || 'div');
  if (cls.length) el.className = cls.join(' ');
  if (attrs && attrs.constructor === Object) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else if (k === 'value') el.value = v;
      else if (k === 'checked') el.checked = !!v;
      else el.setAttribute(k, v === true ? '' : v);
    }
  } else if (attrs != null) kids.unshift(attrs);
  for (const k of kids.flat()) if (k != null && k !== false) el.append(k instanceof Node ? k : String(k));
  return el;
}

async function api(path, method = 'GET', body) {
  const r = await fetch('api/admin/' + path, {
    method, cache: 'no-store',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}

function toast(msg, bad) {
  const t = $('#toast'); t.textContent = msg; t.className = bad ? 'bad' : ''; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 2600);
}

const clone = (x) => JSON.parse(JSON.stringify(x));
const get = (o, path) => path.split('.').reduce((a, k) => (a == null ? undefined : a[k]), o);
function set(o, path, v) {
  const ks = path.split('.'); let a = o;
  for (const k of ks.slice(0, -1)) a = a[k] = (a[k] && typeof a[k] === 'object') ? a[k] : {};
  const last = ks[ks.length - 1];
  if (v === undefined || v === '' || v === null) delete a[last]; else a[last] = v;
}

const SIZES = [
  ['Echo Show 8', 961, 601], ['Echo Show 5', 788, 394], ['Echo Show 15', 1280, 720],
  ['Fire TV / 1080p TV', 960, 540], ['Tablet 1280×800', 1280, 800], ['Laptop', 1440, 900],
];
const integReady = (id) => (S.integrations.find((i) => i.id === id) || {}).ready;
const CATS = ['Photos', 'Home', 'Weather & sky', 'Alerts', 'News & info', 'Sports', 'Media', 'Webcams', 'Fun', 'Other'];

async function load() {
  S = await api('state');
  render();
}

function render() {
  document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('on', b.dataset.tab === tab));
  const warn = !S.password_set && !S.ingress
    ? h('div.banner', 'No admin password: anyone on your network can change this. Set one under Integrations → Admin password.') : null;
  main.replaceChildren(...[warn, tab === 'views' ? viewsPage() : integrationsPage()].filter(Boolean));
}

// ---------------------------------------------------------------- views
function pick(id) {
  cur = id;
  draft = id && S.views[id] ? clone(S.views[id]) : null;
  render();
}

function viewsPage() {
  const ids = Object.keys(S.views);
  if (cur == null && ids.length) { cur = ids[0]; draft = clone(S.views[cur]); }
  const list = h('div.list',
    ids.map((id) => h('button' + (id === cur ? '.on' : ''), { onclick: () => pick(id) }, S.views[id].name, h('small', id))),
    h('button.add', { onclick: newView }, '+ New view'));
  if (!draft) return h('div.views', list, h('div.panel', h('h2', 'Create your first screen'),
    h('p.muted', 'A view is one screen: a URL you point a kiosk browser at (Echo Show with Kiosk Satellite, a tablet with Fully Kiosk, any browser). Pick its size, a photo album and which cards it shows.'),
    h('div.actions', h('button.btn.primary', { onclick: newView }, '+ New view'))));
  return h('div.views', list, viewEditor(), preview());
}

function newView() {
  const name = prompt('Name of the new view (e.g. "Kitchen")');
  if (!name) return;
  let id = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 32) || 'view';
  while (S.views[id]) id += '-2';
  const base = S.views[cur] || {};
  const cards = {};
  for (const c of S.cards) cards[c.id] = c.default_enabled && !c.default_shows;  // sensible start: the general cards
  cur = id;
  draft = { name, width: base.width || 961, height: base.height || 601, album: '', cards, _new: true };
  render();
}

function dirty() {
  if (!draft) return false;
  if (draft._new) return true;
  return canon(draft) !== canon(S.views[cur]);
}

// stable comparison: sorted keys, empty rotation/undefined values ignored (the server drops them too)
function canon(v) {
  const walk = (x) => {
    if (Array.isArray(x)) return x.map(walk);
    if (x && typeof x === 'object') {
      const o = {};
      for (const k of Object.keys(x).sort()) {
        const w = walk(x[k]);
        if (w === undefined || w === null || (k === 'rotation' && !Object.keys(w).length)) continue;
        o[k] = w;
      }
      return o;
    }
    return x;
  };
  return JSON.stringify(walk(v || {}));
}

function markDirty() { const b = $('#save-view'); if (b) b.disabled = !dirty(); }

function viewEditor() {
  const v = draft;
  const sizeSel = h('select', {
    onchange: (e) => {
      const s = SIZES[+e.target.value]; if (!s) return;
      v.width = s[1]; v.height = s[2]; render();
    },
  }, h('option', { value: '' }, 'Custom'),
  SIZES.map((s, i) => h('option', { value: i, selected: s[1] === v.width && s[2] === v.height || null }, `${s[0]} (${s[1]}×${s[2]})`)));
  const num = (key, label, obj = v, help) => h('label.f', label,
    h('input', { type: 'number', value: obj[key] ?? '', placeholder: help || '',
      oninput: (e) => { obj[key] = e.target.value === '' ? undefined : +e.target.value; markDirty(); },
      onchange: () => key === 'width' || key === 'height' ? render() : null }));
  const rot = v.rotation = v.rotation || {};
  const albumSel = h('select', { onchange: (e) => { v.album = e.target.value; markDirty(); } },
    h('option', { value: '' }, 'Photos card default'));
  loadAlbums().then((al) => {
    for (const a of al) albumSel.append(h('option', { value: a.id, selected: a.id === v.album || null }, `${a.name} (${a.count})`));
    if (v.album && !al.some((a) => a.id === v.album)) albumSel.append(h('option', { value: v.album, selected: true }, v.album));
  }).catch((e) => albumSel.append(h('option', { disabled: true }, 'Immich: ' + e.message)));

  const groups = {};
  for (const c of S.cards) (groups[c.category] = groups[c.category] || []).push(c);
  const cardsEl = h('div.cards');
  for (const cat of CATS.filter((k) => groups[k]).concat(Object.keys(groups).filter((k) => !CATS.includes(k)))) {
    cardsEl.append(h('h3', cat));
    for (const c of groups[cat]) cardsEl.append(cardRow(c));
  }
  return h('div.panel',
    h('h2', v.name),
    h('div.row',
      h('label.f', 'Name', h('input', { value: v.name, oninput: (e) => { v.name = e.target.value; markDirty(); } })),
      h('label.f', 'Screen size', sizeSel)),
    h('div.row', num('width', 'Width (CSS px)'), num('height', 'Height (CSS px)')),
    h('label.f', 'Photo album', albumSel),
    h('label.chk', h('input', { type: 'checkbox', checked: !!v.lite, onchange: (e) => { v.lite = e.target.checked || undefined; render(); } }),
      'Low-power screen', h('span.muted.small', ' — no live video, no starfield clock, reloads every 2 h (Echo Show 5, old tablets)')),
    h('h3', 'Rotation'),
    h('div.row',
      num('photos_between', 'Photos between cards', rot, S.rotation.photos_between),
      num('photo_seconds', 'Photo seconds', rot, S.rotation.photo_seconds),
      num('card_seconds', 'Card seconds', rot, S.rotation.card_seconds)),
    h('h3', 'Cards'),
    h('p.small.muted', 'Switches are per view. ⚙ settings are shared by every view.'),
    cardsEl,
    h('div.actions',
      h('button.btn.primary', { id: 'save-view', onclick: saveView, disabled: !dirty() || null }, draft._new ? 'Create view' : 'Save view'),
      draft._new ? null : h('button.btn', { onclick: () => pick(cur) }, 'Revert'),
      h('span.grow'),
      draft._new ? null : h('button.btn.danger', { onclick: delView }, 'Delete view')));
}

function cardRow(c) {
  const v = draft;
  const on = v.cards[c.id] ?? (c.default_enabled && (!c.default_shows || c.default_shows.includes(cur)));
  const missing = c.needs.filter((n) => !integReady(n));
  const kind = c.interrupt ? 'interrupt' : c.layer === 'over' ? 'overlay' : null;
  return h('div.crow',
    h('label.sw', h('input', { type: 'checkbox', checked: on, onchange: (e) => { v.cards[c.id] = e.target.checked; markDirty(); } }), h('span')),
    h('div.nm', h('b', c.name), h('small', c.about)),
    kind ? h('span.tag', kind) : null,
    c.heavy && v.lite ? h('span.tag.warn', { title: 'Skipped: this view is low-power' }, 'off: low-power') : null,
    c.overridden ? h('span.tag.edit', { title: 'Settings changed from the defaults' }, 'edited') : null,
    missing.length ? h('span.tag.warn', { title: 'Needs ' + missing.join(', ') + ' (Integrations)' }, 'needs ' + missing.join(', ')) : null,
    h('button.icon', { title: 'Preview this card', onclick: () => setPreview(c.id) }, '▶'),
    h('button.icon', { title: 'Settings', onclick: () => openCard(c) }, '⚙'));
}

async function saveView() {
  const { _new, ...body } = draft;
  try {
    S = await api('views/' + cur, 'PUT', body);
    draft = clone(S.views[cur]);
    toast('Saved. Screens pick it up within a minute.');
    render();
  } catch (e) { toast(e.message, true); }
}

async function delView() {
  if (!confirm(`Delete the view "${draft.name}"? Screens using ?show=${cur} fall back to the default cards.`)) return;
  try { S = await api('views/' + cur, 'DELETE'); cur = null; draft = null; render(); } catch (e) { toast(e.message, true); }
}

let pvCard = '';
function setPreview(id) { pvCard = id; render(); }

function preview() {
  const v = draft;
  const url = `${S.screen_base || location.origin + '/'}?show=${encodeURIComponent(cur)}`;
  const local = `./?show=${encodeURIComponent(cur)}`;  // relative: also works inside the HA sidebar (ingress)
  const wrap = h('div.pv-wrap');
  const frame = h('iframe', { src: draft._new ? 'about:blank' : local + (pvCard ? '&card=' + pvCard : ''), width: v.width, height: v.height });
  wrap.append(frame);
  const fit = () => {
    const w = wrap.clientWidth || 600;
    const k = w / v.width;
    frame.style.transform = `scale(${k})`;
    wrap.style.height = v.height * k + 12 + 'px';
  };
  requestAnimationFrame(fit);
  new ResizeObserver(fit).observe(wrap);
  return h('div.panel.sticky',
    h('h2', 'Preview', h('span.muted.small', ` ${v.width}×${v.height}`)),
    wrap,
    h('div.actions',
      h('select', { onchange: (e) => setPreview(e.target.value) },
        h('option', { value: '' }, 'Live rotation'),
        S.cards.map((c) => h('option', { value: c.id, selected: c.id === pvCard || null }, c.name))),
      h('button.btn.small', { onclick: () => { frame.src = frame.src; } }, 'Reload')),
    h('h3', 'Kiosk URL'),
    h('div.actions', h('span.url', url),
      h('button.btn.small', { onclick: () => navigator.clipboard.writeText(url).then(() => toast('Copied')) }, 'Copy')),
    draft._new ? h('p.small.muted', 'Create the view to preview it.') :
      h('p.small.muted', 'Saved changes show here after Reload. The preview shows the saved view, not unsaved edits.'));
}

async function loadAlbums() {
  if (!albums) albums = api('albums');
  return albums;
}

async function entityList(domain) {
  if (!ents[domain]) ents[domain] = api('entities?domain=' + encodeURIComponent(domain || ''));
  return ents[domain];
}

// ---------------------------------------------------------------- card settings drawer
function field(f, obj, onchange) {
  const val = get(obj, f.key);
  const upd = (v) => { set(obj, f.key, v); onchange && onchange(); };
  const wrap = (input) => h('label.f', f.label, input, f.help ? h('span.help', f.help) : null);
  switch (f.type) {
    case 'bool':
      return h('label.chk', h('input', { type: 'checkbox', checked: val !== false && val != null, onchange: (e) => upd(e.target.checked) }), f.label);
    case 'number':
      return wrap(h('input', { type: 'number', step: 'any', value: val ?? '', oninput: (e) => upd(e.target.value === '' ? undefined : +e.target.value) }));
    case 'textarea':
      return wrap(h('textarea', { oninput: (e) => upd(e.target.value) }, val ?? ''));
    case 'select':
      return wrap(h('select', { onchange: (e) => upd(e.target.value) },
        h('option', { value: '' }, '—'),
        f.choices.map((c) => { const [v, l] = Array.isArray(c) ? c : [c, c]; return h('option', { value: v, selected: String(v) === String(val) || null }, l); })));
    case 'multi': {
      const sel = new Set((val || []).map(String));
      return h('div', h('label.f', f.label), h('div.multi', f.choices.map((c) => {
        const [v, l] = Array.isArray(c) ? c : [c, c];
        return h('label.chk', h('input', { type: 'checkbox', checked: sel.has(String(v)), onchange: (e) => {
          e.target.checked ? sel.add(String(v)) : sel.delete(String(v));
          upd(f.choices.map((x) => (Array.isArray(x) ? x[0] : x)).filter((x) => sel.has(String(x))));
        } }), l);
      })), f.help ? h('span.help', f.help) : null);
    }
    case 'tags': {
      const help = f.help || (f.choices ? 'Comma separated: ' + f.choices.join(', ') : 'Comma separated');
      return h('label.f', f.label, h('input', { value: (val || []).join(', '),
        oninput: (e) => upd(e.target.value.split(',').map((x) => x.trim()).filter(Boolean)) }), h('span.help', help));
    }
    case 'entity': {
      const id = 'dl-' + (f.domain || 'all');
      const input = h('input', { value: val ?? '', list: id, placeholder: (f.domain || '') + '.…', oninput: (e) => upd(e.target.value.trim()) });
      if (!document.getElementById(id)) {
        const dl = h('datalist', { id }); document.body.append(dl);
        entityList(f.domain).then((es) => es.forEach((x) => dl.append(h('option', { value: x.id }, x.name)))).catch(() => {});
      }
      return wrap(input);
    }
    case 'album': {
      const sel = h('select', { onchange: (e) => upd(e.target.value) }, h('option', { value: '' }, '—'));
      loadAlbums().then((al) => {
        for (const a of al) sel.append(h('option', { value: a.id, selected: a.id === val || null }, `${a.name} (${a.count})`));
      }).catch((e) => sel.append(h('option', { disabled: true }, 'Immich: ' + e.message)));
      return wrap(sel);
    }
    case 'list': return listField(f, obj, onchange);
    default:
      return wrap(h('input', { value: val ?? '', oninput: (e) => upd(e.target.value) }));
  }
}

function listField(f, obj, onchange) {
  if (!Array.isArray(get(obj, f.key))) set(obj, f.key, []);
  const arr = get(obj, f.key);
  const box = h('div');
  const title = (it) => get(it, f.item || f.fields[0].key) || '(new)';
  const draw = (openIdx = -1) => {
    box.replaceChildren(h('label.f', `${f.label} (${arr.length})`));
    arr.forEach((it, i) => {
      const body = h('div.ib', { hidden: i !== openIdx || null });
      const name = h('b', title(it));
      body.append(...f.fields.map((sf) => field(sf, it, () => { name.textContent = title(it); onchange && onchange(); })));
      const move = (d) => (e) => { e.stopPropagation(); const j = i + d; if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; onchange && onchange(); draw(j); };
      box.append(h('div.item',
        h('div.ih', { onclick: () => (body.hidden = !body.hidden) }, name,
          h('button.icon', { title: 'Up', onclick: move(-1) }, '↑'),
          h('button.icon', { title: 'Down', onclick: move(1) }, '↓'),
          h('button.icon', { title: 'Remove', onclick: (e) => { e.stopPropagation(); if (confirm('Remove ' + title(it) + '?')) { arr.splice(i, 1); onchange && onchange(); draw(); } } }, '✕')),
        body));
    });
    box.append(h('button.btn.small', { onclick: () => { arr.push({}); onchange && onchange(); draw(arr.length - 1); } }, '+ Add'));
  };
  draw();
  return box;
}

const DAYS = [['', 'Every day'], ['mon-fri', 'Weekdays'], ['sat-sun', 'Weekends']];

function openCard(c) {
  const opts = clone(c.options);
  const sch = clone(c.schedule);
  const when = sch.when = sch.when || {};
  const days = typeof when.days === 'string' ? when.days : Array.isArray(when.days) ? when.days.join(',') : '';
  const missing = c.needs.filter((n) => !integReady(n));
  const body = h('div.db',
    h('p.muted', c.about),
    missing.length ? h('p', h('span.tag.warn', 'needs ' + missing.join(', ')), ' Set it up under Integrations.') : null,
    c.settings.length ? h('h3', 'Settings') : null,
    c.settings.map((f) => field(f, opts)),
    h('h3', 'When it plays'),
    h('div.row',
      h('label.f', 'Days', h('select', { onchange: (e) => (e.target.value ? (when.days = e.target.value) : delete when.days) },
        DAYS.map(([v, l]) => h('option', { value: v, selected: v === days || null }, l)),
        days && !DAYS.some(([v]) => v === days) ? h('option', { value: days, selected: true }, days) : null)),
      h('label.f', 'Hours', h('input', { value: (when.hours || []).join(', '), placeholder: 'any time, or 06:00-22:00, …',
        oninput: (e) => { const v = e.target.value.split(',').map((x) => x.trim()).filter(Boolean); v.length ? (when.hours = v) : delete when.hours; } }))),
    h('div.row',
      h('label.f', 'Seconds on screen', h('input', { type: 'number', value: sch.duration ?? '', placeholder: S.rotation.card_seconds,
        oninput: (e) => (sch.duration = e.target.value === '' ? null : +e.target.value) })),
      c.interrupt
        ? h('label.f', 'Same item again after (min)', h('input', { type: 'number', value: sch.repeat_minutes ?? '', placeholder: 10,
          oninput: (e) => (sch.repeat_minutes = e.target.value === '' ? null : +e.target.value) }))
        : h('label.f', 'At most every (min)', h('input', { type: 'number', value: sch.every_minutes ?? '', placeholder: 'every cycle',
          oninput: (e) => (sch.every_minutes = e.target.value === '' ? null : +e.target.value) }))),
    c.interrupt ? h('p.small.muted', 'Interrupt card: cuts in whenever it has something to show.') : null);
  drawer.replaceChildren(
    h('div.dh', h('h2', c.name, h('button.icon', { onclick: closeDrawer, title: 'Close' }, '✕')),
      h('div.small.muted', c.id + ' · ' + c.type + ' · shared by every view')),
    body,
    h('div.df',
      h('button.btn.primary', { onclick: async () => {
        if (!when.days && !when.hours) sch.when = null;  // null = any time (overrides a default window)
        try { S = await api('cards/' + c.id, 'PUT', { options: opts, schedule: sch }); toast('Saved'); closeDrawer(); render(); }
        catch (e) { toast(e.message, true); }
      } }, 'Save'),
      h('button.btn', { onclick: closeDrawer }, 'Cancel'),
      h('span.grow', { style: 'flex:1' }),
      c.overridden ? h('button.btn.danger', { onclick: async () => {
        if (!confirm('Reset ' + c.name + ' to the shipped defaults?')) return;
        try { S = await api('cards/' + c.id, 'DELETE'); toast('Reset'); closeDrawer(); render(); } catch (e) { toast(e.message, true); }
      } }, 'Reset to defaults') : null));
  drawer.hidden = false;
}

function closeDrawer() { drawer.hidden = true; drawer.replaceChildren(); }
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !drawer.hidden) closeDrawer(); });

// ---------------------------------------------------------------- integrations
function integrationsPage() {
  const loc = clone(S.location || {});
  const used = (id) => S.cards.filter((c) => c.needs.includes(id)).map((c) => c.name);
  return h('div',
    h('div.integ',
      h('div.panel',
        h('h2', 'Home location'),
        h('p.small.muted', 'Weather alerts, air quality, rain and sky use this unless a card sets its own.' + (S.location_from_ha ? ' Now: Home Assistant\'s location (leave blank to keep that).' : '')),
        h('div.row',
          h('label.f', 'Latitude', h('input', { type: 'number', step: 'any', value: loc.lat ?? '', oninput: (e) => (loc.lat = e.target.value) })),
          h('label.f', 'Longitude', h('input', { type: 'number', step: 'any', value: loc.lon ?? '', oninput: (e) => (loc.lon = e.target.value) }))),
        h('p.small.muted', 'Two decimals (about 1 km) is plenty, and keeps the exact house out of third-party requests.'),
        h('div.actions', h('button.btn.primary', { onclick: async () => {
          try { S = await api('location', 'PUT', loc); toast('Saved'); } catch (e) { toast(e.message, true); }
        } }, 'Save'))),
      S.integrations.map((i) => integPanel(i, used(i.id))),
      passwordPanel()));
}

function integPanel(i, usedBy) {
  const vals = {}, clear = [];
  const res = h('span.result');
  return h('div.panel',
    h('h2', i.name, h(i.ready ? 'span.tag.ok' : 'span.tag.warn', i.ready ? 'ready' : 'not set')),
    h('p.small.muted', i.about, usedBy.length ? ' Used by: ' + usedBy.join(', ') + '.' : ''),
    i.fields.map((f) => {
      const src = f.source === 'admin' ? 'set here' : f.source === 'app' ? 'automatic (Home Assistant app)' : f.source === 'env' ? 'from the environment' : f.set ? 'default' : f.optional ? 'optional' : 'not set';
      const input = f.secret
        ? h('input', { type: 'password', autocomplete: 'new-password', placeholder: f.set ? `•••••• ${f.hint} (${src}) — type to replace` : (f.optional ? 'optional' : 'not set'),
          oninput: (e) => (vals[f.key] = e.target.value) })
        : h('input', { value: f.source ? f.value || '' : '', placeholder: f.placeholder || f.default || '', oninput: (e) => (vals[f.key] = e.target.value) });
      return h('label.f', f.label, input,
        h('span.help', [f.help, f.secret ? '' : src].filter(Boolean).join(' · '),
          f.source === 'admin' ? h('a', { href: '#', onclick: (e) => { e.preventDefault(); clear.push(f.key); toast('Will clear on Save'); } },
            ' · use the deployment value') : null));
    }),
    h('div.actions',
      h('button.btn.primary', { onclick: async () => {
        try { S = await api('integrations/' + i.id, 'PUT', { values: vals, clear }); toast('Saved'); render(); }
        catch (e) { toast(e.message, true); }
      } }, 'Save'),
      h('button.btn', { onclick: async () => {
        res.className = 'result'; res.textContent = 'testing…';
        try { const r = await api('integrations/' + i.id + '/test', 'POST', {}); res.className = 'result ' + (r.ok ? 'ok' : 'bad'); res.textContent = (r.ok ? '✓ ' : '✕ ') + r.detail; }
        catch (e) { res.className = 'result bad'; res.textContent = e.message; }
      } }, 'Test saved'),
      res));
}

function passwordPanel() {
  let pw = '';
  return h('div.panel',
    h('h2', 'Admin password', h(S.password_set ? 'span.tag.ok' : 'span.tag.warn', S.password_set ? 'set' : 'open')),
    h('p.small.muted', S.app ? 'Only needed to open this page directly on port 8099; the Home Assistant sidebar needs no extra login.' : 'Protects this page (any user name). The screens themselves need no login.'),
    h('label.f', 'New password', h('input', { type: 'password', autocomplete: 'new-password', oninput: (e) => (pw = e.target.value) })),
    h('div.actions', h('button.btn.primary', { onclick: async () => {
      try { await api('password', 'PUT', { password: pw }); toast('Password changed: sign in again'); setTimeout(() => location.reload(), 1200); }
      catch (e) { toast(e.message, true); }
    } }, 'Change')));
}

document.querySelectorAll('nav button').forEach((b) => b.addEventListener('click', () => {
  if (tab === 'views' && dirty() && !confirm('Discard unsaved changes to this view?')) return;
  tab = b.dataset.tab; render();
}));
window.addEventListener('beforeunload', (e) => { if (dirty()) e.preventDefault(); });
load().catch((e) => main.replaceChildren(h('p', 'Could not load: ' + e.message)));
