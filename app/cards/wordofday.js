// Word of the day: the word letters drop in, then pronunciation, definition, example.
export function render(d, { h }) {
  const word = h('div.wd-word', ...[...d.word].map((c, i) => h('span', { style: { animationDelay: 0.2 + i * 0.07 + 's' } }, c)));
  return h('div.panel.wd',
    h('div.head', h('h1', 'Word of the day'), h('span.label', 'Merriam-Webster')),
    h('div.wd-main', word, h('div.wd-pron', [d.pron && `\\${d.pron}\\`, d.pos].filter(Boolean).join('  ·  ')),
      h('div.wd-def', d.def), d.example && h('div.wd-ex', '“' + d.example + '”')));
}
