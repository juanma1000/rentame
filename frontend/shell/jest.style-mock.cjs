// CSS imports have no runtime meaning under jsdom (Jest doesn't execute a
// browser stylesheet engine) — mapped here so `import './button.css'` (from
// `@rentame/ui`) resolves to an empty module instead of Jest trying to parse
// raw CSS as JavaScript. Same pattern as `inmuebles-app`.
module.exports = {};
