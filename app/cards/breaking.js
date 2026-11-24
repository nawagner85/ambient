// Breaking news: red banner, big headline.
export function render(d, { h }) {
  return h('div.brk', h('div.brk-bar', h('span.brk-dot'), 'BREAKING NEWS'),
    h('div.brk-title', d.title), h('div.brk-src', `${d.source} · ${d.mins < 1 ? 'just now' : d.mins + ' min ago'}`));
}
