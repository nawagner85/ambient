// Weather: big now + 5-day strip.
export function render(d, { h, icon, label, day }) {
  const sub = [d.humidity != null && `Humidity ${d.humidity}%`, d.wind != null && `Wind ${Math.round(d.wind)} ${d.wind_unit}`]
    .filter(Boolean).join(' · ');
  const fx = h('div.wx-fx');
  const c = d.cond || '';
  const n = /pouring|lightning/.test(c) ? 70 : /rain/.test(c) ? 45 : /snow|hail/.test(c) ? 40 : 0;
  for (let i = 0; i < n; i++) {
    fx.append(h(/snow|hail/.test(c) ? 'i.flake' : 'i.drop', { style: {
      left: Math.random() * 100 + '%', animationDelay: -Math.random() * 3 + 's',
      animationDuration: (/snow/.test(c) ? 4 + Math.random() * 4 : 0.6 + Math.random() * 0.5) + 's' } }));
  }
  if (/cloud|fog|rain|pour/.test(c)) for (let i = 0; i < 4; i++) {
    fx.append(h('i.cloud', { style: { top: 5 + i * 14 + '%', animationDelay: -i * 9 + 's', animationDuration: 30 + i * 8 + 's', opacity: 0.05 + i * 0.02 } }));
  }
  if (/sunny|clear/.test(c)) fx.append(h('i.rays'));
  return h('div.panel', fx,
    h('div.head', h('h1', 'Weather'), h('span.label', d.place)),
    h('div.wx-now', h('div.big', icon(d.cond)),
      h('div', h('div.temp', `${Math.round(d.temp)}°`), h('div.cond', label(d.cond)), h('div.sub', sub))),
    h('div.wx-days', ...d.days.map((x, i) => h('div.wx-day',
      h('div.label', i === 0 ? 'Today' : day(x.date)), h('div.i', icon(x.cond)),
      h('div.hl', `${Math.round(x.hi)}° `, x.lo != null && h('span', `${Math.round(x.lo)}°`)),
      h('div.pp', x.precip ? `💧 ${x.precip}%` : '')))));
}
