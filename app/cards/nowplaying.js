// Now playing: album art over a blurred copy of itself, title/artist/album, bouncing EQ bars, live progress bar.
const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
export function render(d, { h }) {
  const bar = h('div.np-fill'), cur = h('span'), tot = h('span', d.dur ? mmss(d.dur) : '');
  const root = h('div.np',
    d.art && h('img.np-bg', { src: d.art }),
    h('div.np-row',
      d.art ? h('img.np-art', { src: d.art }) : h('div.np-art.none', '♪'),
      h('div.np-info',
        h('div.np-eq', ...Array.from({ length: 5 }, (_, i) => h('i', { style: { animationDelay: -(i * 0.23) + 's' } })),
          h('span.label', `Now playing${d.room ? ' · ' + d.room : ''}`)),
        h('div.np-title', d.title), h('div.np-artist', d.artist), d.album && h('div.np-album', d.album),
        d.dur ? h('div.np-prog', h('div.np-track', bar), h('div.np-times', cur, tot)) : null)));
  if (d.dur) {
    const t0 = performance.now(), base = (d.pos || 0) + (Date.now() / 1000 - d.at);
    const step = () => {
      if (!root.isConnected && performance.now() - t0 > 2000) return;
      const p = Math.min(d.dur, base + (performance.now() - t0) / 1000);
      bar.style.width = (p / d.dur * 100) + '%'; cur.textContent = mmss(p);
      setTimeout(step, 500);
    };
    step();
  }
  return root;
}
