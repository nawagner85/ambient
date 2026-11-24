// Sky: sun arc with the sun at its current spot, moon drawn at its real phase, aurora chance.
function moonSvg(m) {
  // lit fraction drawn with an ellipse terminator; waxing = lit on the right
  const r = 60, k = 1 - 2 * (m.illum / 100), rx = Math.abs(k) * r, sweepLit = m.waxing ? 1 : 0;
  const bulge = k > 0 ? (m.waxing ? 0 : 1) : (m.waxing ? 1 : 0);
  return `<svg viewBox="-70 -70 140 140"><defs><radialGradient id="mg" cx="40%" cy="35%"><stop offset="0" stop-color="#fffbe8"/><stop offset="1" stop-color="#d9d2b6"/></radialGradient></defs>
    <circle r="${r}" fill="#24303d"/>
    <path d="M0,-${r} A${r},${r} 0 0 ${sweepLit} 0,${r} A${rx},${r} 0 0 ${bulge} 0,-${r}Z" fill="url(#mg)"/>
    <circle r="${r}" fill="none" stroke="rgba(255,255,255,.15)"/></svg>`;
}
export function render(d, { h }) {
  const arc = document.createElement('div'); arc.className = 'sk-arc';
  const a = Math.PI * (1 - d.sunfrac), x = 150 + 130 * Math.cos(a), y = 140 - 120 * Math.sin(a);
  arc.innerHTML = `<svg viewBox="0 0 300 160"><path d="M20 140 A130 120 0 0 1 280 140" class="path"/>
    <line x1="0" y1="140" x2="300" y2="140" class="hz"/>
    <circle cx="${x}" cy="${y}" r="11" class="sun ${d.up ? '' : 'down'}"/></svg>`;
  const moon = document.createElement('div'); moon.className = 'sk-moon'; moon.innerHTML = moonSvg(d.moon);
  return h('div.panel.sky',
    h('div.sk-stars', ...Array.from({ length: 40 }, () => h('i', { style: { left: Math.random() * 100 + '%', top: Math.random() * 60 + '%', animationDelay: -Math.random() * 4 + 's' } }))),
    h('div.head', h('h1', 'Sky'), h('span.label', `Day length ${d.daylight} (${d.change})`)),
    h('div.sk',
      h('div.sk-sun', arc, h('div.sk-times', h('div', h('span.label', 'Sunrise'), h('b', d.sunrise)), h('div', h('span.label', 'Golden hour'), h('b', d.golden)), h('div', h('span.label', 'Sunset'), h('b', d.sunset)))),
      h('div.sk-right', moon, h('div.sk-mname', d.moon.name), h('div.sk-msub', `${d.moon.illum}% lit · full moon ${d.moon.full_in <= 1 ? (d.moon.full_in === 0 ? 'tonight' : 'tomorrow') : 'on ' + d.moon.full_date}`),
        d.aurora ? h('div.sk-aurora', `🌌 Aurora: ${d.aurora} (Kp ${d.kp})`) : d.kp != null && h('div.sk-kp', `Aurora: unlikely tonight (Kp ${d.kp})`))));
}
