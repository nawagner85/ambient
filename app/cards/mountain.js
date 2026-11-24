// Is the mountain out? Space Needle view toward Rainier (portrait slice, shown as a landscape band) + verdict.
const SAY = { out: 'The mountain is out! 🏔️', peeking: 'The mountain is peeking ⛅', hiding: 'The mountain is hiding ☁️' };
const SUB = { out: 'Go look south — Rainier in all its glory.', peeking: 'A ghost of Rainier through the haze.', hiding: 'Rainier is taking a cloud day.' };
export function render(d, { h }) {
  return h('div.cam.mtn',
    h('div.pic', h('img.bg', { src: d.src }), h('img.fg', { src: d.src })),
    h('div.foot', h('div', h('div.verdict.' + (d.state === 'hiding' ? 'hiding' : 'out'), SAY[d.state] || SAY.hiding),
      h('div.place', SUB[d.state] || '')), h('div.local', h('span.label', 'Space Needle cam'), h('b', d.taken || ''))));
}
