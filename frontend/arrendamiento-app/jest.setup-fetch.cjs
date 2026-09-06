'use strict';
/**
 * Stub global.fetch for the jsdom test environment.
 *
 * jsdom's window does not expose a native `fetch` in this project's
 * configuration, but the API service tests use
 * `jest.spyOn(global, 'fetch')` which requires the property to exist
 * on the global object before spying.  We stub it here so every test
 * starts with a spy-able `global.fetch`; individual tests override the
 * behavior with `.mockResolvedValueOnce(...)` as needed.
 *
 * The stub throws on unmocked calls so accidental real-network requests
 * surface immediately instead of silently hanging.
 *
 * Copied verbatim from inmuebles-app/jest.setup-fetch.cjs.
 */
if (typeof globalThis.fetch !== 'function') {
  globalThis.fetch = function fetch() {
    return Promise.reject(
      new TypeError(
        '[test-stub] global.fetch was called without a mock. ' +
          'Use jest.spyOn(global, "fetch").mockResolvedValueOnce(...) in the test.',
      ),
    );
  };
}
