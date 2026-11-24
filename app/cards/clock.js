// Fun clocks, a nod to the Chumby's Domo Klock, Space Clock and RoboClock. One style per appearance, in turn.
let turn = 0;
const NS = 'http://www.w3.org/2000/svg';
const pad = (n) => String(n).padStart(2, '0');
const parts = () => { const d = new Date(); const h = d.getHours() % 12 || 12; return { h: String(h), m: pad(d.getMinutes()), ap: d.getHours() < 12 ? 'AM' : 'PM', s: d.getSeconds(), d }; };
function svg(markup, cls) { const w = document.createElement('div'); w.className = cls; w.innerHTML = markup; return w; }
// Run fn every ms while el is on screen.
function live(el, fn, ms) { fn(); const t = setInterval(() => (el.isConnected || !el.parentNode ? fn() : clearInterval(t)), ms); setTimeout(() => { if (!el.isConnected) clearInterval(t); }, 60000); return t; }

function domo(h) {
  const el = h('div.clk.domo');
  const guy = svg(`<svg viewBox="0 0 200 240" xmlns="${NS}" overflow="visible">
    <defs><pattern id="fur" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6 L3 0 L6 6" fill="none" stroke="#6b3a1c" stroke-width=".8" opacity=".35"/></pattern>
      <clipPath id="mouthclip"><rect x="40" y="96" width="120" height="82" rx="6"/></clipPath></defs>
    <ellipse cx="100" cy="232" rx="70" ry="7" fill="rgba(60,30,10,.25)" class="shadow"/>
    <g class="body">
      <rect x="22" y="20" width="156" height="206" rx="34" fill="#8B4A22"/><rect x="22" y="20" width="156" height="206" rx="34" fill="url(#fur)"/>
      <g class="eyes"><ellipse cx="70" cy="70" rx="9" ry="11" fill="#111"/><ellipse cx="130" cy="70" rx="9" ry="11" fill="#111"/>
        <g class="pupils"><circle cx="73" cy="66" r="2.5" fill="#fff"/><circle cx="133" cy="66" r="2.5" fill="#fff"/></g></g>
      <g clip-path="url(#mouthclip)">
        <rect x="40" y="96" width="120" height="82" fill="#B3121B"/><rect x="40" y="150" width="120" height="28" fill="#7a0b12"/>
        <path class="teeth-top" d="M40 96 L55 116 L70 96 L85 116 L100 96 L115 116 L130 96 L145 116 L160 96 Z" fill="#fff"/>
        <path class="teeth-bot" d="M40 178 L55 158 L70 178 L85 158 L100 178 L115 158 L130 178 L145 158 L160 178 Z" fill="#fff"/>
      </g>
    </g></svg>`, 'domo-guy');
  const time = h('div.clk-time'), ap = h('div.clk-sub'), sec = h('span.clk-sec');
  el.append(guy, h('div.domo-side', h('div', time, sec), ap, h('div.label', 'Domo Klock')));
  let last = '';
  live(el, () => { const p = parts(); time.textContent = `${p.h}:${p.m}`; time.style.display = 'inline-block';
    sec.textContent = String(p.s).padStart(2, '0'); sec.classList.remove('tick'); void sec.offsetWidth; sec.classList.add('tick'); ap.textContent = p.ap + ' · ' + p.d.toLocaleDateString('en-US', { weekday: 'long' });
    if (last && last !== p.m) { guy.classList.remove('chomp'); void guy.offsetWidth; guy.classList.add('chomp'); } last = p.m; }, 1000);
  return el;
}

function space(h) {
  const el = h('div.clk.space');
  const cv = document.createElement('canvas');
  const time = h('div.clk-time'), sub = h('div.clk-sub');
  const sec = h('span.clk-sec');
  el.append(cv, h('div.planet'), h('div.ship', '🛸'), h('div.shoot'), h('div.space-hud', h('div.label', 'Ship time'), h('div', time, sec), sub));
  const stars = Array.from({ length: 140 }, () => ({ x: Math.random() * 2 - 1, y: Math.random() * 2 - 1, z: Math.random() }));
  const ctx = cv.getContext('2d');
  let raf, then = 0;
  const frame = (t) => {
    if (!el.isConnected && then) return;  // stopped once removed
    raf = requestAnimationFrame(frame);
    if (t - then < 33) return; then = t;   // ~30 fps is plenty
    const w = cv.width = cv.clientWidth, hh = cv.height = cv.clientHeight;
    ctx.fillStyle = '#02040a'; ctx.fillRect(0, 0, w, hh);
    for (const s of stars) {
      s.z -= 0.012; if (s.z <= 0.02) { s.x = Math.random() * 2 - 1; s.y = Math.random() * 2 - 1; s.z = 1; }
      const k = 0.5 / s.z, px = w / 2 + s.x * k * w / 2, py = hh / 2 + s.y * k * hh / 2, r = Math.max(0.4, (1 - s.z) * 2.2);
      ctx.fillStyle = `rgba(200,225,255,${1 - s.z})`; ctx.beginPath(); ctx.arc(px, py, r, 0, 6.3); ctx.fill();
    }
  };
  raf = requestAnimationFrame(frame);
  live(el, () => { const p = parts(); time.textContent = `${p.h}:${p.m}`; time.style.display = 'inline-block';
    sec.textContent = String(p.s).padStart(2, '0'); sec.classList.remove('tick'); void sec.offsetWidth; sec.classList.add('tick');
    const doy = Math.floor((p.d - new Date(p.d.getFullYear(), 0, 0)) / 864e5);
    sub.textContent = `${p.ap} · Stardate ${p.d.getFullYear()}.${String(doy).padStart(3, '0')}`; }, 1000);
  return el;
}

function robo(h) {
  const el = h('div.clk.robo');
  const tiles = [0, 1, 2, 3].map(() => h('div.tile'));
  const colon = h('div.colon', ':');
  const bot = svg(`<svg viewBox="0 0 300 150" xmlns="${NS}">
    <g class="arm left"><rect x="60" y="40" width="70" height="14" rx="7" fill="#9fb3c8"/><circle cx="130" cy="47" r="10" fill="#56789a"/><path d="M52 32 l-14 -10 M52 62 l-14 10" stroke="#9fb3c8" stroke-width="8" stroke-linecap="round"/></g>
    <g class="arm right"><rect x="170" y="40" width="70" height="14" rx="7" fill="#9fb3c8"/><circle cx="170" cy="47" r="10" fill="#56789a"/><path d="M248 32 l14 -10 M248 62 l14 10" stroke="#9fb3c8" stroke-width="8" stroke-linecap="round"/></g>
    <line x1="150" y1="18" x2="150" y2="4" stroke="#9fb3c8" stroke-width="4"/><circle cx="150" cy="4" r="5" fill="#F59A8E" class="led"/>
    <rect x="115" y="18" width="70" height="56" rx="12" fill="#243C54" stroke="#9fb3c8" stroke-width="4"/>
    <circle cx="137" cy="44" r="8" fill="#62B7E3" class="led"/><circle cx="163" cy="44" r="8" fill="#62B7E3" class="led"/>
    <rect x="135" y="60" width="30" height="5" rx="2" fill="#9fb3c8"/>
    <rect x="120" y="78" width="60" height="60" rx="10" fill="#34506A"/><rect x="132" y="92" width="36" height="8" rx="3" fill="#6FCF97" class="led"/>
    </svg>`, 'robo-bot');
  const sub = h('div.clk-sub'), sec = h('div.robo-sec');
  el.append(h('div.robo-tiles', tiles[0], tiles[1], colon, tiles[2], tiles[3]), bot, sec, sub);
  let last = '';
  live(el, () => {
    const p = parts(); const s = p.h.padStart(2, ' ') + p.m;
    [...s].forEach((c, i) => { if (tiles[i].textContent !== c) { if (last) { tiles[i].classList.remove('swap'); void tiles[i].offsetWidth; tiles[i].classList.add('swap'); } tiles[i].textContent = c; } });
    tiles[0].style.display = p.h.length === 1 ? 'none' : '';
    colon.style.opacity = p.s % 2 ? 0.25 : 1; sub.textContent = `${p.ap} · RoboClock`;
    sec.textContent = `SEC ${String(p.s).padStart(2, '0')}  ${'▮'.repeat(Math.floor(p.s / 6))}${'▯'.repeat(10 - Math.floor(p.s / 6))}`;
    if (p.s % 2 === 0) { const vis = tiles.filter((t) => t.style.display !== 'none'); const t = vis[Math.floor(Math.random() * vis.length)];
      t.classList.remove('hop'); void t.offsetWidth; t.classList.add('hop'); }
    last = s;
  }, 1000);
  return el;
}

// Flip: a split-flap tribute to the Chumby "12H Flip Clock with secs - Ivory". Ivory cards, hinged halves that fall,
// seconds flipping every tick; on the minute the cards riffle like a real flap board and the whole clock gives a clack.
function flipcard(cls) {
  const c = document.createElement('div'); c.className = 'fc ' + cls;
  c.innerHTML = '<div class="fc-h fc-t"><b></b></div><div class="fc-h fc-b"><b></b></div>'
    + '<div class="fc-h fc-t fc-ft"><b></b></div><div class="fc-h fc-b fc-fb"><b></b></div><i class="fc-pin l"></i><i class="fc-pin r"></i>';
  const [st, sb, ft, fb] = [...c.querySelectorAll('b')];
  let cur = null, timers = [];
  const flip = (v, ms) => {
    if (cur === null) { st.textContent = sb.textContent = ft.textContent = fb.textContent = v; cur = v; return; }
    if (v === cur) return;
    st.textContent = v; sb.textContent = cur; ft.textContent = cur; fb.textContent = v; cur = v;
    c.style.setProperty('--fd', ms + 'ms'); c.classList.remove('go'); void c.offsetWidth; c.classList.add('go');
  };
  // riffle: a quick run of random flaps that lands on v
  const riffle = (v, n, max) => { timers.forEach(clearTimeout); timers = [];
    for (let i = 0; i < n; i++) timers.push(setTimeout(() => flip(max ? pad(Math.floor(Math.random() * max)) : String(1 + Math.floor(Math.random() * 12)), 55), i * 125));
    timers.push(setTimeout(() => flip(v, 160), n * 125)); };
  return { el: c, flip, riffle, get busy() { return timers.length > 0; }, clear() { timers = []; } };
}

function flip(h) {
  const el = h('div.clk.flip');
  const H = flipcard('hh'), M = flipcard('mm'), S = flipcard('ss');
  const ap = h('div.fl-ap'), date = h('div.fl-date');
  H.el.append(ap);
  const colon = h('div.fl-colon', h('i'), h('i'));
  const face = h('div.fl-face', h('div.fl-row', H.el, colon, M.el, S.el), date);
  el.append(h('div.fl-glow'), face, h('div.fl-sheen'));
  let last = null, lastH = null, busyUntil = 0;
  live(el, () => {
    const p = parts(), now = Date.now();
    ap.textContent = p.ap; date.textContent = p.d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    if (last !== null && last !== p.m) {            // minute change: riffle + clack
      M.riffle(p.m, 9, 60); S.riffle(pad(p.s), 9, 60);
      if (lastH !== p.h) H.riffle(p.h, 12, 0);
      busyUntil = now + 1900;
      face.classList.remove('clack'); void face.offsetWidth; face.classList.add('clack');
      el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    } else if (now > busyUntil) {
      H.clear(); M.clear(); S.clear();
      H.flip(p.h, 260); M.flip(p.m, 260); S.flip(pad(p.s), 200);
    }
    last = p.m; lastH = p.h;
  }, 250);
  return el;
}

// Isle: a tribute to the Chumby "Danny Marooned" clock (chumby industries, 2009). Danny, a bearded castaway in a white
// vest and red shorts, potters about a one-palm sandbar under a pale sky; the time sits huge and ghostly on the horizon.
// Each minute the old digits sink into the sea and the new ones bob up; a log drifts ashore for his raft pile and he
// cheers... until every fourth minute a wave takes the pile and he starts again. Poor Danny.
function isle(h) {
  const el = h('div.clk.isle');
  const leaf = (r, s, fill, mirror, dur, begin) => `<g transform="${mirror ? 'scale(-1 1) ' : ''}rotate(${r}) scale(${s})"><g>
      <path d="M0 0 C-12 -13 -34 -15 -54 -1 L-47 -2 L-50 4 L-40 0 L-41 7 L-31 2 L-30 8 L-22 3 L-19 7 L-12 2 C-7 3 -3 2 0 0 Z" fill="${fill}"/>
      <path d="M0 0 C-14 -9 -32 -10 -52 -1" fill="none" stroke="rgba(40,70,20,.45)" stroke-width="1"/>
      <animateTransform attributeName="transform" type="rotate" values="0;${mirror ? 4 : -4};0" dur="${dur}s" begin="${begin}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g></g>`;
  const scene = svg(`<svg viewBox="0 0 480 300" preserveAspectRatio="xMidYMin slice" xmlns="${NS}">
    <defs>
      <linearGradient id="isl-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2448a3"/><stop offset=".45" stop-color="#172f74"/><stop offset="1" stop-color="#101d4c"/></linearGradient>
      <radialGradient id="isl-glint" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#4f7fe0" stop-opacity=".55"/><stop offset="1" stop-color="#4f7fe0" stop-opacity="0"/></radialGradient>
      <radialGradient id="isl-sunglow" cx=".5" cy=".5" r=".5"><stop offset=".55" stop-color="#ffc21a" stop-opacity=".45"/><stop offset="1" stop-color="#ffc21a" stop-opacity="0"/></radialGradient>
      <clipPath id="isl-sky"><rect x="-200" y="-50" width="880" height="175.5"/></clipPath>
    </defs>
    <rect x="-200" y="125" width="880" height="400" fill="url(#isl-sea)"/>
    <ellipse cx="220" cy="140" rx="230" ry="60" fill="url(#isl-glint)"/>
    <rect x="-200" y="-50" width="880" height="175" fill="#b2dde4"/>
    <g class="isl-glints">${[28, 66, 104, 150, 187, 236, 270, 352, 400, 446].map((x, i) => `<rect x="${x}" y="${128 + (i % 3) * 2.5}" width="${4 + (i % 2) * 3}" height=".9" rx=".45" fill="#dbe9ff" style="animation-delay:${(i * 0.37) % 2.6}s"/>`).join('')}</g>
    <g class="isl-ship"><path d="M0 0 L26 0 L23 4 L3 4 Z" fill="#e9eef3"/><rect x="5" y="-4" width="15" height="4" fill="#f6f8fa"/><rect x="8" y="-7" width="8" height="3" fill="#f6f8fa"/><rect x="13" y="-11" width="3" height="4" fill="#d9534f"/></g>
    <g class="isl-time" clip-path="url(#isl-sky)"></g>
    <g class="isl-sun"><circle cx="382" cy="100" r="26" fill="url(#isl-sunglow)" class="isl-halo"/><circle cx="382" cy="100" r="16" fill="#ffae00"/></g>
    <g class="isl-rip a"><path d="M160 224 Q 172 236 214 240 M176 232 Q 196 242 236 244"/><path d="M362 236 Q 396 232 410 220 M346 243 Q 386 240 402 230"/></g>
    <g class="isl-rip b"><path d="M150 226 Q 166 242 210 247"/><path d="M370 242 Q 404 236 418 222"/></g>
    <g class="isl-wet"><ellipse cx="285" cy="214" rx="113" ry="23" fill="#8fb4e6" opacity=".45"/></g>
    <ellipse cx="285" cy="212" rx="106" ry="19.5" fill="#f4dd9c"/>
    <ellipse cx="278" cy="208" rx="86" ry="11" fill="#f8e6b1" opacity=".7"/>
    <g fill="#d8bb72">${Array.from({ length: 46 }, (_, i) => { const a = i * 2.39996, r = Math.sqrt((i + .5) / 46); return `<circle cx="${(285 + Math.cos(a) * r * 96).toFixed(1)}" cy="${(212 + Math.sin(a) * r * 16).toFixed(1)}" r=".7"/>`; }).join('')}</g>
    <path d="M318 204 C 330 200 352 201 366 205 C 350 206 336 209 318 208 Z M316 205 C 300 199 286 200 276 203 C 292 207 304 208 316 207 Z" fill="#c9a95c" opacity=".55" class="isl-shade"/>
    <g class="isl-logs"></g>
    <g class="isl-palm">
      <path d="M309 205 C 313 170 318 130 318 97 L 326 97 C 327 130 323 170 322 205 Z" fill="#8a5a32"/>
      <path d="M318 98 L 326 98 C 326.6 125 325 150 323 178 L 320 178 C 322 150 322 125 322 98 Z" fill="#6f4425" opacity=".55"/>
      <g stroke="#5e391d" stroke-width="1.3" opacity=".7">${[110, 124, 138, 152, 166, 180, 194].map((y) => `<path d="M${(319 - (y - 98) * 0.06).toFixed(1)} ${y} l7 -2.5"/>`).join('')}</g>
      <g transform="translate(322 97)"><g>
        ${leaf(-26, .82, '#4f8a2a', false, 5.2, 0.4)}${leaf(-24, .86, '#4f8a2a', true, 5.6, 1.1)}
        ${leaf(4, 1, '#6ba83a', false, 4.6, 0)}${leaf(2, 1.02, '#6ba83a', true, 4.9, 0.7)}
        ${leaf(32, .86, '#8cc443', false, 5.0, 1.5)}${leaf(30, .84, '#9bd04c', true, 4.4, 0.2)}
        ${leaf(70, .6, '#5f9a32', false, 5.8, 0.9)}${leaf(64, .58, '#7fbb3f', true, 5.3, 2.0)}
        <animateTransform attributeName="transform" type="rotate" values="-1.5;1.5;-1.5" dur="7s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g></g>
    </g>
    <g class="isl-drift"><g class="isl-bob"></g></g>
    <g class="dny" style="transform: translate(262px, 210px)"><g class="dn-face"><g transform="scale(.92)">
      <ellipse cx="0" cy="0" rx="11" ry="2.6" fill="rgba(80,50,10,.22)" class="dn-shadow"/>
      <g class="dn-body">
      <g class="dn-stand">
        <g class="dn-hipL" transform="translate(-3.6 -17)"><g class="dn-legL"><rect x="-2.3" y="0" width="4.6" height="16" rx="2.2" fill="#d8925f"/><ellipse cx="-.6" cy="15.6" rx="3.4" ry="1.7" fill="#c97f4d"/></g></g>
        <g class="dn-hipR" transform="translate(3.6 -17)"><g class="dn-legR"><rect x="-2.3" y="0" width="4.6" height="16" rx="2.2" fill="#e09d69"/><ellipse cx=".9" cy="15.6" rx="3.4" ry="1.7" fill="#d08752"/></g></g>
      </g>
      <g class="dn-cross"><path d="M-14 -1 C -12 -7 -4 -8 0 -5 C 4 -8 12 -7 14 -1 C 8 1 -8 1 -14 -1 Z" fill="#d8925f"/><path d="M-9 -9 L 9 -9 L 11 -3 L -11 -3 Z" fill="#c8302a"/></g>
      <g class="dn-upper">
        <path d="M-8 -27 L 8 -27 L 8.5 -16 L 1 -16 L 0 -19 L -1 -16 L -8.5 -16 Z" fill="#cf342c"/>
        <rect x="-8" y="-27" width="16" height="2.2" fill="#a92621"/>
        <path d="M-7.5 -42 C -6.5 -44 -4 -44 -3.6 -42 C -2 -39.5 2 -39.5 3.6 -42 C 4 -44 6.5 -44 7.5 -42 L 8 -26.5 L -8 -26.5 Z" fill="#fbfbf8"/>
        <path d="M-3.6 -42 C -2 -39.5 2 -39.5 3.6 -42 L 2.5 -44 L -2.5 -44 Z" fill="#d8925f"/>
        <g transform="translate(0 -44)"><g class="dn-head">
          <circle cx="-9.6" cy="-8" r="2.4" fill="#d08752"/>
          <circle cx="0" cy="-9" r="10.6" fill="#e3a06c"/>
          <path d="M-10.8 -10 C -12 -21 8 -24 11 -13 C 9 -16 4 -17 -1 -15 C -3 -12 -7 -12 -8 -9 Z" fill="#1d1a18"/>
          <path d="M-10.6 -8 C -10 3 -4 6 2 5.5 C 8 5 11.5 0 10.6 -6 C 9 -3 7 -2.5 4.5 -3 C 2 -3.6 -1 -3 -3 -2 C -6 -3 -8 -5 -10.6 -8 Z" fill="#1d1a18"/>
          <path d="M1 -1.2 C 3 0 5.6 0 7 -1.6 C 5.8 1.2 2.4 1.4 1 -1.2 Z" fill="#f2f2ee"/>
          <path d="M-1.5 -12.6 L 3.4 -13.4 M 6.5 -13.4 L 9.6 -12.4" stroke="#1d1a18" stroke-width="1.3" stroke-linecap="round"/>
          <g class="dn-eyes"><ellipse cx="1.6" cy="-9.6" rx="1.35" ry="1.9" fill="#1d1a18"/><ellipse cx="7.6" cy="-9.6" rx="1.25" ry="1.8" fill="#1d1a18"/></g>
          <path d="M9.8 -8.6 C 12.4 -7.6 12.6 -5.2 10 -4.6 Z" fill="#c97f4d"/>
        </g></g>
        <g class="dn-shL" transform="translate(-8.6 -40.5)"><g class="dn-armL"><rect x="-2.1" y="-1" width="4.2" height="15" rx="2.1" fill="#d08752"/><circle cx="0" cy="14.5" r="2.6" fill="#d8925f"/></g></g>
        <g class="dn-shR" transform="translate(8.6 -40.5)"><g class="dn-armR"><rect x="-2.1" y="-1" width="4.2" height="15" rx="2.1" fill="#e09d69"/><circle cx="0" cy="14.5" r="2.6" fill="#e3a06c"/></g></g>
      </g>
    </g></g></g></g>
    <g class="isl-wave"><path d="M-90 12 C -60 8 -30 -4 0 -14 C 18 -19 34 -15 38 -6 C 40 0 34 3 29 0 C 27 -5 20 -6 16 -1 C 40 9 110 10 180 6 L 180 16 L -90 16 Z" fill="#7ea4e0" opacity=".9"/><path d="M-60 8 C -30 2 -10 -8 6 -12 C 20 -15 32 -12 35 -6 C 30 -9 22 -9 17 -4 C 12 2 -20 8 -60 11 Z M20 4 C 60 9 120 9 170 5 C 120 12 60 12 20 4 Z" fill="#f2f8ff"/></g>
    <g class="isl-splash"></g>
  </svg>`, 'isl-scene');
  el.append(scene);
  const S = scene.firstElementChild, q = (s) => S.querySelector(s);
  const mk = (tag, attrs) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };
  const timeG = q('.isl-time'), logsG = q('.isl-logs'), drift = q('.isl-drift'), bob = q('.isl-bob'), splash = q('.isl-splash');
  const dn = q('.dny'), face = q('.dn-face'), wave = q('.isl-wave'), ship = q('.isl-ship');

  // --- the time: one <text> per glyph in fixed slots along the horizon, so a changed digit can sink and a new one rise
  const DW = 77, CW = 34, X0 = 6, BASE = 122;
  let shown = '';
  const glyph = (c, x, cls) => { const t = mk('text', { x, y: BASE, 'text-anchor': 'middle', class: 'isl-d' + (cls ? ' ' + cls : '') }); t.textContent = c; timeG.append(t); return t; };
  const layout = (s) => { let x = X0; return [...s].map((c) => { const w = c === ':' ? CW : DW; const cx = x + w / 2; x += w; return cx; }); };
  const setTime = (s, animate) => {
    const xs = layout(s), old = [...timeG.querySelectorAll('.isl-d:not(.sink)')];
    if (!animate || s.length !== shown.length) { timeG.textContent = ''; [...s].forEach((c, i) => glyph(c, xs[i])); shown = s; return; }
    [...s].forEach((c, i) => {
      if (c === shown[i]) return;
      old[i].classList.add('sink'); setTimeout(() => old[i].remove(), 1300);
      const n = glyph(c, xs[i], 'rise');
      timeG.insertBefore(n, old[i]);
      setTimeout(() => plop(xs[i]), 1250);
    });
    shown = s;
  };
  const plop = (x) => {   // a ring and a few drops where a digit breaks the surface
    const g = mk('g', { class: 'isl-plop', transform: `translate(${x} 127)` });
    g.append(mk('ellipse', { class: 'ring', cx: 0, cy: 0, rx: 30, ry: 3.5 }));
    [-16, -7, 5, 15].forEach((dx, i) => { const c = mk('circle', { class: 'drop', cx: 0, cy: 0, r: 1.8 - (i % 2) * .5 }); c.style.setProperty('--dx', dx + 'px'); c.style.setProperty('--dy', -(10 + (i % 2 ? 6 : 12)) + 'px'); g.append(c); });
    splash.append(g); setTimeout(() => g.remove(), 1600);
  };

  // --- the raft pile: one log per minute, three max; the fourth minute's wave takes them
  const SLOTS = [[214, 214, -4], [226, 208, 3], [219, 203, -2]];
  const logSvg = () => '<rect x="-15" y="-3" width="30" height="6" rx="3" fill="#94592f"/><rect x="-15" y="-3" width="30" height="2" rx="1" fill="#ad7140"/><ellipse cx="15" cy="0" rx="2.3" ry="3" fill="#d9a56e"/><ellipse cx="15" cy="0" rx="1" ry="1.4" fill="#a8703e"/>';
  const pile = (n) => { logsG.innerHTML = ''; for (let i = 0; i < n; i++) { const g = mk('g', { transform: `translate(${SLOTS[i][0]} ${SLOTS[i][1]}) rotate(${SLOTS[i][2]})` }); g.innerHTML = logSvg(); logsG.append(g); } };

  // --- Danny's little life: walk, gaze out to sea (hand to brow), sit by the palm, stand about, blink
  let pos = { x: 262, y: 210 }, dir = 1, act = 'idle', until = 0, queue = [];
  const pose = (p) => { dn.classList.remove('walk', 'look', 'sit', 'cheer', 'sad'); if (p !== 'idle') dn.classList.add(p); act = p; };
  const faceTo = (d) => { dir = d; face.style.transform = `scaleX(${d})`; };
  const walkTo = (x, y, now) => {
    const dist = Math.hypot(x - pos.x, y - pos.y); if (dist < 3) { until = now; return; }
    const sec = dist / 24; faceTo(x < pos.x ? -1 : 1);
    dn.style.transition = `transform ${sec.toFixed(2)}s linear`; dn.style.transform = `translate(${x}px, ${y}px)`;
    pos = { x, y }; pose('walk'); until = now + sec * 1000;
  };
  const rnd = (a, b) => a + Math.random() * (b - a);
  const spot = () => { const x = rnd(210, 362); return { x, y: x > 300 && x < 335 ? rnd(209, 217) : rnd(203, 217) }; };
  const plan = (now) => {
    if (queue.length) { const [k, a, b] = queue.shift(); if (k === 'walk') walkTo(a, b, now); else { pose(k); until = now + a; if (b) faceTo(b); } return; }
    const r = Math.random();
    if (r < .42) { const s = spot(); walkTo(s.x, s.y, now); }
    else if (r < .66) { pose('look'); faceTo(Math.random() < .5 ? -1 : 1); until = now + rnd(3500, 5500); }
    else if (r < .82) { queue = [['walk', 298, 208], ['sit', rnd(5000, 8000)]]; plan(now); }
    else { pose('idle'); until = now + rnd(1500, 3200); }
  };
  const event = (now, gone) => {   // minute change: log ashore + cheer, or the wave + a sad little shuffle
    queue = [];
    if (gone) {
      wave.classList.remove('go'); void wave.getBBox(); wave.classList.add('go');
      setTimeout(() => logsG.classList.add('wash'), 900);
      setTimeout(() => { logsG.classList.remove('wash'); pile(0); }, 2400);
      queue = [['look', 1300, -1], ['sad', 3200, -1], ['idle', 800]]; until = 0; plan(now);
      return;
    }
    const n = logsG.childElementCount, slot = SLOTS[Math.min(n, 2)];
    bob.innerHTML = `<g transform="rotate(${slot[2]})">${logSvg()}</g>`;
    drift.style.transition = 'none'; drift.style.transform = 'translate(120px, 246px)'; drift.style.opacity = '1'; void drift.getBBox();
    drift.style.transition = 'transform 3.2s cubic-bezier(.3,.1,.4,1)'; drift.style.transform = 'translate(196px, 230px)';
    setTimeout(() => { drift.style.transition = 'transform .6s cubic-bezier(.3,1.6,.6,1)'; drift.style.transform = `translate(${slot[0]}px, ${slot[1]}px)`; }, 3200);
    setTimeout(() => { drift.style.transition = 'none'; drift.style.opacity = '0'; pile(Math.min(n + 1, 3)); }, 3850);
    queue = [['walk', 252, Math.min(Math.max(pos.y, 205), 214)], ['look', 9000, -1]]; until = 0; plan(now);
    setTimeout(() => { queue = [['cheer', 2800], ['idle', 700]]; until = 0; }, 3800);
  };

  // ship on the horizon now and then (Danny never notices it)
  if (Math.random() < .45) { ship.classList.add('go'); ship.style.animationDelay = `-${rnd(0, 30).toFixed(1)}s`; }

  let lastM = null;
  live(el, () => {
    const p = parts(), now = Date.now(), s = `${p.h}:${p.m}`;
    if (lastM === null) { setTime(s, false); pile(+p.m % 4 === 0 ? 0 : +p.m % 4); }
    else if (lastM !== p.m) { setTime(s, true); event(now, +p.m % 4 === 0); }
    lastM = p.m;
    if (now >= until) plan(now);
  }, 250);
  return el;
}

export function render(d, { h }) {
  const styles = (d && d.styles && d.styles.length) ? d.styles : ['domo', 'space', 'robo'];
  const style = new URLSearchParams(location.search).get('style') || styles[turn++ % styles.length];  // ?style= for previews
  return ({ domo, space, robo, flip, isle }[style] || domo)(h);
}
