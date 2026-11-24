// Scores: head-to-head rows — away logo + name + score | status | score + name + home logo.
// Same weight for every team name; the winner's score is bright with a ▶, your team gets an Emi-blue underline.
export function render(d, { h }) {
  const team = (s, g, side) => {
    const won = g.state === 'post' && s.winner, lost = g.state === 'post' && !s.winner;
    const score = g.state !== 'pre' ? h('span.sc-score' + (lost ? '.lost' : ''), (won && side === 'home' ? '' : ''), s.score ?? '') : null;
    const parts = [s.logo ? h('img', { src: s.logo }) : h('div.sc-dot'), h('span.sc-name' + (s.ours ? '.ours' : ''), s.name), score];
    if (won) parts.push(h('span.sc-win', side === 'away' ? '◀' : '▶'));
    return h('div.sc-side.' + side, ...(side === 'away' ? parts : parts.reverse()));
  };
  return h('div.panel',
    h('div.head', h('h1', 'Scores'), h('span.label', d.games.some((g) => g.state === 'in') ? '● Live' : 'Your teams')),
    h('div.sc-list', ...d.games.map((g) => h('div.sc.' + g.state,
      team(g.sides[0], g, 'away'),
      h('div.sc-status', g.state === 'pre' ? g.when : g.state === 'in' ? g.detail : 'Final',
        g.state !== 'post' && g.broadcast && h('small', g.broadcast)),
      team(g.sides[1], g, 'home')))));
}
