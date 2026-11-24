// Top news: lead story with photo on the left, ticker-style headline list on the right.
export function render(d, { h }) {
  return h('div.panel.news',
    h('div.head', h('h1', 'Top news'), h('span.label', 'Google News · US')),
    h('div.nw',
      d.lead && h('div.nw-lead', h('img', { src: d.lead.img }), h('div.nw-cap', h('b', d.lead.title), h('span', `${d.lead.source} · ${d.lead.ago}`))),
      h('div.nw-list', ...d.heads.map((x, i) => h('div.nw-item', { style: { animationDelay: 0.3 + i * 0.18 + 's' } },
        h('b', x.title), h('span', [x.source, x.ago].filter(Boolean).join(' · ')))))));
}
