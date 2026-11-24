// Weather alert: hazard-striped banner, event, headline, short description.
const ICON = [['Wind', '🌬️'], ['Flood', '🌊'], ['Winter', '❄️'], ['Snow', '❄️'], ['Ice', '🧊'], ['Heat', '🔥'], ['Fire', '🔥'], ['Air', '😷'], ['Thunder', '⛈️'], ['Tornado', '🌪️'], ['Fog', '🌫️'], ['Tsunami', '🌊']];
export function render(d, { h }) {
  const icon = (ICON.find(([k]) => d.event.includes(k)) || [0, '⚠️'])[1];
  const until = d.until ? new Date(d.until).toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' }) : '';
  return h('div.wxa.' + (d.severity || '').toLowerCase(),
    h('div.wxa-stripe'),
    h('div.wxa-body',
      h('div.wxa-top', h('span.wxa-icon', icon), h('span.label', `Weather alert · ${d.severity}`)),
      h('div.wxa-event', d.event), until && h('div.wxa-until', `Until ${until}`),
      h('div.wxa-desc', d.desc), d.more > 0 && h('div.wxa-more', `+${d.more} more alert${d.more > 1 ? 's' : ''}`)));
}
