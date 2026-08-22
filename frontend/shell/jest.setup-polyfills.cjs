/**
 * Jest environment polyfills for `shell`.
 *
 * jsdom's global scope does not provide `TextEncoder`/`TextDecoder`, which
 * `react-router` v8's `server-runtime/crypto.js` module references at import
 * time (even though `shell` never uses react-router's server/SSR APIs).
 * Node.js itself exposes both globally, so we simply copy them onto the
 * jsdom global before any test module (and therefore react-router) loads.
 *
 * Added alongside the HU-008 frontend tests (EntradaPage/LoginPage/
 * RegistroPage), which are the first `shell` tests to render `MemoryRouter`
 * + `Routes` directly instead of mocking `react-router`.
 */
const { TextEncoder, TextDecoder } = require('util');

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}

/**
 * jsdom's global scope (jest-environment-jsdom) does not implement `fetch`
 * (jsdom itself has no network stack), unlike Node's own global scope which
 * has provided `fetch` since Node 18. `services/usuarios.api.ts` and
 * `services/agencias.api.ts` call the native `fetch` directly (same pattern
 * as `inmuebles-app/src/services/*.api.ts`), and every test that exercises
 * them replaces it via `jest.spyOn(global, 'fetch').mockResolvedValueOnce(...)`
 * — which requires the property to already exist on the object being spied
 * on, but never calls through to a real implementation (every test mocks
 * every call it makes). A full polyfill (e.g. via `undici`) pulls in Node
 * internals (WHATWG Streams, `MessagePort`, ...) that jsdom's global scope
 * doesn't provide either — not worth chasing for something that is always
 * mocked. A throwing stub is enough to make `global.fetch` a spy-able
 * property; any test that forgets to mock a `fetch` call fails loudly.
 */
if (typeof global.fetch === 'undefined') {
  global.fetch = () => {
    throw new Error(
      'global.fetch was called without being mocked. Tests must mock fetch via ' +
        "jest.spyOn(global, 'fetch') before triggering any code path that calls it.",
    );
  };
}
