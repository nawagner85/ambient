// US markets: three tiles, animated sparkline draw + count-up numbers.
const fmt = (n, d = 2) => Number(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
function spark(h, pts, up) {
  const NS = 'http://www.w3.org/2000/svg';
  if (pts.length < 2) return h('div');
  const lo = Math.min(...pts), hi = Math.max(...pts), w = 200, ht = 60;
  const xy = pts.map((p, i) => `${(i / (pts.length - 1)) * w},${ht - ((p - lo) / ((hi - lo) || 1)) * ht}`).join(' ');
  const wrap = document.createElement('div'); wrap.className = 'mk-spark';
  wrap.innerHTML = `<svg viewBox="0 -4 ${w} ${ht + 8}" preserveAspectRatio="none" xmlns="${NS}">
    <polygon points="0,${ht + 4} ${xy} ${w},${ht + 4}" class="area ${up ? 'mk-up' : 'mk-dn'}"/>
    <polyline points="${xy}" class="line ${up ? 'mk-up' : 'mk-dn'}" pathLength="100"/></svg>`;
  return wrap;
}
function countUp(el, to, digits) {
  const t0 = performance.now(), from = to * 0.985;
  const step = (t) => { const k = Math.min(1, (t - t0) / 1200); el.textContent = fmt(from + (to - from) * (1 - Math.pow(1 - k, 3)), digits); if (k < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
export function render(d, { h }) {
  return h('div.panel',
    h('div.head', h('h1', 'Markets'), h('span.label', d.state === 'open' ? '● Market open' : 'Market closed · last session')),
    h('div.mk', ...d.indices.map((x) => {
      const up = x.chg >= 0, p = h('div.mk-price');
      countUp(p, x.price, 2);
      return h('div.mk-tile.' + (up ? 'mk-up' : 'mk-dn'), h('div.mk-name', x.name), p,
        h('div.mk-chg', `${up ? '▲' : '▼'} ${fmt(Math.abs(x.chg))}  (${up ? '+' : '−'}${fmt(Math.abs(x.pct))}%)`), spark(h, x.spark, up));
    })));
}
