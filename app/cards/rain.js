// Rain soon: falling drops, "Rain around 3:40 PM", next-hour bars.
export function render(d, { h }) {
  const fx = h('div.wx-fx');
  for (let i = 0; i < 50; i++) fx.append(h('i.drop', { style: { left: Math.random() * 100 + '%', animationDelay: -Math.random() * 3 + 's', animationDuration: 0.7 + Math.random() * 0.5 + 's' } }));
  const max = Math.max(...d.series, 0.5);
  return h('div.panel.rain', fx,
    h('div.head', h('h1', '☔ Rain soon'), h('span.label', 'Next hour')),
    h('div.rn', h('div.rn-big', d.mins <= 5 ? 'Rain any minute' : `Rain around ${d.at}`),
      h('div.rn-sub', `${d.heavy ? 'Heavy at times' : 'Light to moderate'} · in about ${d.mins} min — grab the laundry & an umbrella`),
      h('div.rn-bars', ...d.series.map((v, i) => h('i', { style: { height: Math.max(4, v / max * 100) + '%', animationDelay: i * 0.08 + 's' } })))));
}
