/**
 * Custom Jest transformer for the rentame-inmuebles-app workspace.
 *
 * Wraps @swc/jest and pre-processes source files to replace `import.meta.hot`
 * (a Vite HMR extension) with `false` before SWC compiles them to CommonJS.
 *
 * React-router v8 ships pure ESM bundles that reference `import.meta.hot` in
 * their SSR modules.  SWC handles `import.meta.url` in CJS transforms but
 * leaves other `import.meta.*` properties intact, causing Node.js to throw
 * "Cannot use 'import.meta' outside a module" when running tests.
 *
 * This preprocessor is safe for tests: HMR never runs in a Jest environment.
 */

'use strict';

const { createTransformer } = require('@swc/jest');

const swcOptions = {
  jsc: {
    parser: { syntax: 'typescript', tsx: true },
    transform: { react: { runtime: 'automatic' } },
    target: 'es2022',
  },
  module: { type: 'commonjs' },
};

const inner = createTransformer(swcOptions);

module.exports = {
  process(sourceText, sourcePath, options) {
    const preprocessed = sourceText
      // Replace Vite HMR flag with `false` so SWC produces valid CJS output.
      .replace(/import\.meta\.hot/g, 'false')
      // Replace import.meta.env with an empty object (covers Vite env vars).
      .replace(/import\.meta\.env/g, '({})');

    return inner.process(preprocessed, sourcePath, options);
  },

  getCacheKey(sourceText, sourcePath, options) {
    // Include the preprocessed text in the cache key so a change in
    // preprocessing logic invalidates the cache correctly.
    const preprocessed = sourceText
      .replace(/import\.meta\.hot/g, 'false')
      .replace(/import\.meta\.env/g, '({})');

    return inner.getCacheKey(preprocessed, sourcePath, options);
  },
};
