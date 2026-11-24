// Air quality: big AQI dial in its category colour, smoke flag, 24 h trend bars.
export function render(d, { h }) {
  const pct = Math.min(1, d.aqi / 300);
  const dial = document.createElement('div'); dial.className = 'aq-dial';
  dial.innerHTML = `<svg viewBox="0 0 200 120"><path d="M20 110 A80 80 0 0 1 180 110" class="track"/>
    <path d="M20 110 A80 80 0 0 1 180 110" class="val" style="stroke:${d.color};stroke-dasharray:${251 * pct} 999"/></svg>`;
  const max = Math.max(...d.trend, 60);
  return h('div.panel',
    h('div.head', h('h1', d.smoke ? 'Wildfire smoke' : 'Air quality'), h('span.label', 'US AQI · now')),
    h('div.aq', h('div.aq-left', dial, h('div.aq-num', { style: { color: d.color } }, d.aqi), h('div.aq-cat', d.cat)),
      h('div.aq-right',
        d.smoke && h('div.aq-smoke', '🔥 Smoke in the air — PM2.5 ' + Math.round(d.pm25) + ' µg/m³'),
        h('div.label', 'Next 24 hours' + (d.peak ? ` · peak ${d.peak}` : '')),
        h('div.aq-bars', ...d.trend.map((v, i) => h('i', { style: { height: (v / max * 100) + '%', background: v > 100 ? '#EB5757' : v > 50 ? '#F2C94C' : '#6FCF97', animationDelay: i * 0.03 + 's' } }))))));
}
