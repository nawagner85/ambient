// Coming up: tear-off date tiles, today/tomorrow highlighted, countdowns, holidays muted.
export function render(d, { h }) {
  return h('div.panel',
    h('div.head', h('h1', 'Coming up'), h('span.label', 'Our crazy life')),
    h('div.cal-list', ...d.events.map((e, i) => h('div.cal' + (e.days <= 1 ? '.soon' : '') + (e.kind === 'holiday' ? '.hol' : ''), { style: { animationDelay: 0.2 + i * 0.12 + 's' } },
      h('div.cal-date', h('span', e.month), h('b', e.dom)),
      h('div.cal-what', h('b', e.title), h('span', [e.when, e.time, e.where].filter(Boolean).join(' · '))),
      h('div.cal-in', e.days === 0 ? 'Today' : e.days === 1 ? 'Tomorrow' : `in ${e.days} days`)))));
}
