// Upcoming games: day, time, opponent, channel.
export function render(d, { h }) {
  return h('div.panel',
    h('div.head', h('h1', 'Coming up'), h('span.label', 'Your teams · next 7 days')),
    h('div.up-list', ...d.games.map((g) => h('div.up',
      h('img', { src: g.logo }),
      h('div.up-who', h('b', g.team), h('span', g.vs)),
      h('div.up-when', h('b', g.day), h('span', g.tbd ? 'Time TBD' : g.time)),
      h('div.up-tv', g.tv || '—')))));
}
