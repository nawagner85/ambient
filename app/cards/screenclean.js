// Emi pops up, licks the glass three times (smudges appear), ducks away; a squeegee wipes it clean. ~11 s.
export function render(d, { h }) {
  const smears = h('div.scl-smears',
    ...[[50, 58, -8], [39, 52, 12], [61, 55, -18], [47, 46, 25]].map(([x, y, r], i) =>
      h('div.scl-smear', { style: { left: x + '%', top: y + '%', transform: `translate(-50%,-50%) rotate(${r}deg)`, animationDelay: (1.5 + i * 1.3) + 's' } })));
  return h('div.scl',
    smears,
    h('div.scl-head', h('img', { src: d.emi }), h('div.scl-tongue')),
    h('div.scl-squeegee', h('div.scl-blade'), h('div.scl-handle')),
    h('div.scl-done', '✨ ', d.caption, ' ✨'));
}
