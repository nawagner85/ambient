// This day in history: three entries dealt in, big year, thumbnail.
export function render(d, { h }) {
  return h('div.panel',
    h('div.head', h('h1', 'This day in history'), h('span.label', d.date)),
    h('div.hi-list', ...d.items.map((x, i) => h('div.hi', { style: { animationDelay: 0.25 + i * 0.35 + 's' } },
      x.img ? h('img', { src: x.img }) : h('div.hi-noimg', '📜'),
      h('div.hi-txt', h('div.hi-year', x.year, h('span', ` · ${x.ago} years ago`)), h('div', x.text))))));
}
