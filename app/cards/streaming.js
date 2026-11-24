// New to stream / Streaming this week: blurred hero backdrop, a row of posters dealt in one by one with service logos.
export function render(d, { h }) {
  const hero = d.items.find((x) => x.backdrop);
  return h('div.st',
    hero && h('img.st-bg', { src: hero.backdrop }),
    h('div.panel.st-panel',
      h('div.head', h('h1', d.kind === 'movie' ? 'New to stream' : 'Streaming this week'), h('span.label', d.kind === 'movie' ? 'Movies · your services' : 'New episodes · your services')),
      h('div.st-row', ...d.items.map((x, i) => h('div.st-card', { style: { animationDelay: 0.2 + i * 0.15 + 's' } },
        h('div.st-poster', h('img', { src: x.poster }), h('img.st-logo', { src: x.logo })),
        h('div.st-title', x.title), h('div.st-meta', [x.service, x.rating ? '★ ' + x.rating : ''].filter(Boolean).join(' · ')))))));
}
