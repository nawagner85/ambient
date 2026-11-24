// Zoltar: velvet booth with chasing marquee bulbs, a swirling crystal ball, and a fortune that types itself out.
export function render(d, { h }) {
  const ball = document.createElement('div');
  ball.className = 'zl-ball';
  ball.innerHTML = '<div class="zl-glow"></div><div class="zl-glow two"></div>';
  const row = (cls) => h('div.zl-bulbs.' + cls, ...Array.from({ length: 11 }, (_, i) => h('i', { style: { animationDelay: (i % 3) * 0.25 + 's' } })));
  const bulbs = [row('top'), row('bot')];
  const text = h('p');
  const lucky = h('div.zl-lucky', 'Lucky number ', h('b', d.lucky));
  lucky.style.opacity = 0;
  // Type the fortune once the card is actually on screen (it may be pre-built hidden), ~7 s max whatever its length.
  const per = Math.min(60, 7000 / Math.max(1, d.fortune.length));
  let i = 0, started = false, tries = 0;
  const tick = () => {
    if (!root.isConnected) return;
    text.textContent = d.fortune.slice(0, ++i);
    if (i < d.fortune.length) setTimeout(tick, per * (0.7 + Math.random() * 0.6));
    else lucky.style.opacity = 1;
  };
  const wait = () => {
    if (started) return;
    const slide = root.closest('.slide');
    if (slide && slide.classList.contains('in') && !slide.classList.contains('pre')) { started = true; setTimeout(tick, 1400); }
    else if (++tries < 900) setTimeout(wait, 200);  // give up after 3 min (pre-built card that was never shown)
  };
  setTimeout(wait, 50);
  const root = h('div.zl',
    h('div.zl-booth', h('div.zl-sign', bulbs, 'ZOLTAR', h('small', 'SPEAKS')), ball, h('div.zl-stand')),
    h('div.zl-card', h('div.label', 'Your fortune'), text, lucky));
  root.dataset.seconds = Math.ceil(1.4 + 1 + (per * d.fortune.length) / 1000 + 7);  // reveal + typing + 7 s to read
  return root;
}
