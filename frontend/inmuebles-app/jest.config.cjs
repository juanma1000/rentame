/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  // Runs before the test framework initialises: stubs global.fetch so that
  // jest.spyOn(global, 'fetch') works in the jsdom environment, which does
  // not expose a native fetch on its window by default.
  setupFiles: ['<rootDir>/jest.setup-fetch.cjs', '<rootDir>/jest.setup-url.cjs'],
  transform: {
    // Use the custom jest-transform wrapper for TypeScript/TSX sources.
    // For JS/MJS files from react-router (pure ESM, no CJS variant) the same
    // wrapper pre-processes `import.meta.hot` → `false` before SWC compiles
    // them to CommonJS so they work in the jsdom test environment.
    '^.+\\.(ts|tsx|js|mjs)$': '<rootDir>/jest-transform.cjs',
  },
  // By default Jest skips all node_modules. react-router v8, react-leaflet
  // and its @react-leaflet/core dependency are pure ESM and must be
  // transformed to CJS for the jsdom test environment.
  transformIgnorePatterns: ['/node_modules/(?!(react-router|react-leaflet|@react-leaflet/core)/)'],
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  testMatch: ['<rootDir>/src/**/__tests__/**/*.test.{ts,tsx}'],
  moduleNameMapper: {
    // Resolve @rentame/auth to TypeScript source so @swc/jest can transform it.
    // This avoids issues with the workspace symlink + transformIgnorePatterns.
    '^@rentame/auth$': '<rootDir>/../packages/auth/src/index.ts',
    '^@rentame/auth/(.*)$': '<rootDir>/../packages/auth/src/$1',
    '^@/(.*)$': '<rootDir>/src/$1',
    // CSS is not executable JS — stub it out (see jest.style-mock.cjs).
    '\\.css$': '<rootDir>/jest.style-mock.cjs',
    // Image assets resolve to a real URL only under Rspack's bundler — stub
    // them out under Jest (see jest.asset-mock.cjs).
    '\\.(png|jpe?g|svg)$': '<rootDir>/jest.asset-mock.cjs',
  },
};
