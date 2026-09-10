// Image imports resolve to a real file path under Rspack's `asset/resource`
// module type — under Jest there's no bundler emitting a file, so this
// stubs them out to a deterministic string (same idea as jest.style-mock.cjs
// for CSS).
module.exports = 'test-file-stub';
