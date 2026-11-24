// Photo slide: one photo (cover, faces kept in frame) or two portraits side by side; date + place bottom-left.
export function render(slide, { h }) {
  const one = (p) => {
    const pos = p.focus ? `${p.focus[0]}% ${Math.min(p.focus[1], 60)}%` : '50% 40%';
    // a single portrait on a landscape screen: show it whole over a blurred copy of itself
    if (p.portrait && slide.photos.length === 1) {
      return h('div.ph', h('img.bg', { src: p.src }), h('img.kb', { src: p.src, style: { position: 'absolute', inset: 0, objectFit: 'contain', '--kx': '0%', '--ky': '-2%' } }));
    }
    // slow pan + zoom toward a random side, anchored on the faces
    const kx = (Math.random() * 6 - 3).toFixed(1) + '%', ky = (Math.random() * 4 - 2).toFixed(1) + '%';
    return h('div.ph', h('img.kb', { src: p.src, style: { objectPosition: pos, transformOrigin: pos, '--kx': kx, '--ky': ky } }));
  };
  const first = slide.photos[0];
  return h('div.photo', ...slide.photos.map(one),
    (first.date || first.place) && h('div.meta', first.place && h('b', first.place), first.date));
}
