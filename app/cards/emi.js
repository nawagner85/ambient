// Today's Secret Life of Emi episode.
export function render(d, { h }) {
  return h('div.emi', h('img', { src: d.img }), h('div.tag', 'The Secret Life of Emi'), h('div.cap', d.caption));
}
