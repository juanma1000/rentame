// CSS imports have no runtime meaning under jsdom (Jest doesn't execute a
// browser stylesheet engine) — mapped here so `import './forms.css'` resolves
// to an empty module instead of Jest trying to parse raw CSS as JavaScript.
module.exports = {};
