// Commute: one row per route, colored by delay over the usual drive.
export function render(d, { h, time }) {
  return h('div.panel',
    h('div.head', h('h1', 'Commute'), h('span.label', 'Waze · now')),
    h('div.cm-list', ...d.routes.map((r) => h('div.cm.' + r.level,
      h('div.who', h('b', `${r.name} → ${r.to}`), h('span', `via ${r.via} · arrive ${time(new Date(r.arrive * 1000))}`)),
      h('div', h('div.mins', `${r.minutes}`, h('small', ' min')),
        h('div.delay', r.delay >= 2 ? `+${r.delay} min vs usual` : 'Clear'))))));
}
