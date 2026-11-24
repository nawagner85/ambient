// New on Plex: posters dealt in, Plex-amber accent, when each arrived.
export function render(d, { h }) {
  return h('div.st.plex',
    h('img.st-bg', { src: d.items[0].poster }),
    h('div.panel.st-panel',
      h('div.head', h('h1', h('span.plex-mark', '▶'), ' New on Plex'), h('span.label', 'Recently added')),
      h('div.st-row', ...d.items.map((x, i) => h('div.st-card', { style: { animationDelay: 0.2 + i * 0.15 + 's' } },
        h('div.st-poster', h('img', { src: x.poster }), h('div.plex-tag', x.kind)),
        h('div.st-title', x.title), h('div.st-meta', x.sub ? `${x.sub}` : ''), h('div.st-meta.plex-ago', x.ago))))));
}
