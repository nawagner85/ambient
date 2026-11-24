// Live webcam, muted: YouTube embed, HLS <video> (hls.js), or a refreshing still. Name + local time in a footer.
let hlsLoading = null;
const loadHls = () => hlsLoading || (hlsLoading = new Promise((ok, bad) => {
  const s = document.createElement('script'); s.src = 'vendor/hls.light.min.js'; s.onload = ok; s.onerror = bad; document.head.append(s);
}));

function player(d, h) {
  if (d.kind === 'youtube') {
    const q = new URLSearchParams({ autoplay: 1, mute: 1, controls: 0, playsinline: 1, rel: 0, modestbranding: 1,
      iv_load_policy: 3, disablekb: 1, fs: 0, enablejsapi: 1, origin: location.origin });
    return h('iframe.yt', { src: `https://www.youtube.com/embed/${d.src}?${q}`, allow: 'autoplay; encrypted-media',
      referrerpolicy: 'strict-origin-when-cross-origin', frameborder: 0, 'data-ready': 'load' });
  }
  if (d.kind === 'hls') {
    const v = h('video.fg', { muted: '', autoplay: '', playsinline: '', 'data-ready': 'playing' });
    v.muted = true;
    if (v.canPlayType('application/vnd.apple.mpegurl')) v.src = d.src;
    else loadHls().then(() => {
      const hls = new window.Hls({ maxBufferLength: 10, lowLatencyMode: false });
      hls.loadSource(d.src); hls.attachMedia(v);
      const t = setInterval(() => { if (!v.isConnected && v.dataset.shown) { hls.destroy(); clearInterval(t); } }, 2000);
    }).catch(() => {});
    v.addEventListener('playing', () => { v.dataset.shown = 1; });
    return v;
  }
  return h('img.fg', { src: d.src });
}

export function render(d, { h }) {
  return h('div.cam',
    h('div.pic.video', player(d, h), h('div.live', '● LIVE')),
    h('div.foot', h('div', h('div.name', d.name), h('div.place', d.place)),
      d.local && h('div.local', h('span.label', 'Local time'), h('b', d.local))));
}
