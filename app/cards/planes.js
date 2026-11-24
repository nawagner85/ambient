// Plane overhead: the whole photo on top (never cropped: contain over a blurred copy), details in a footer bar.
const DEG = { N: 0, NE: 45, E: 90, SE: 135, S: 180, SW: 225, W: 270, NW: 315 };
export function render(d, { h }) {
  const who = `${d.airline || d.owner || 'Aircraft'} ${d.flight || d.callsign}`;
  const alt = d.altitude_ft ? `${Number(d.altitude_ft).toLocaleString('en-US')} ft` : '';
  const mph = d.speed_kt ? `${Math.round(d.speed_kt * 1.15078)} mph` : '';
  const what = [d.aircraft || d.type_code, alt, mph, d.planes_in_range > 1 && `${d.planes_in_range} planes in view`].filter(Boolean).join(' · ');
  return h('div.pl',
    d.photo
      ? h('div.pic', h('img.bg', { src: d.photo }), h('img.fg', { src: d.photo }))
      : h('div.pic.none', '✈️'),
    h('div.foot',
      h('div.look', h('span.label', 'Overhead now'),
        h('div.big', 'Look ', d.bearing, ' ', h('span.arrow', { style: { transform: `rotate(${DEG[d.bearing] || 0}deg)` } }, '↑')),
        h('div.up', `${d.elevation_deg}° up`)),
      h('div.info',
        h('div.who', who),
        d.origin && h('div.route', `${d.origin} → ${d.destination}`),
        h('div.what', what))));
}
