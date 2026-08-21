import { rspack, type Configuration } from '@rspack/core';
import { ModuleFederationPlugin } from '@module-federation/enhanced/rspack';

const isDev = process.env['NODE_ENV'] !== 'production';

const config: Configuration = {
  entry: './src/main.tsx',
  output: {
    // 'auto' lets Rspack infer the public path from the request URL —
    // works for both dev server and static deployments.
    publicPath: 'auto',
  },
  mode: isDev ? 'development' : 'production',
  devtool: isDev ? 'cheap-module-source-map' : false,
  module: {
    rules: [
      {
        test: /\.(tsx?|jsx?)$/,
        use: {
          loader: 'builtin:swc-loader',
          options: {
            jsc: {
              parser: { syntax: 'typescript', tsx: true },
              transform: { react: { runtime: 'automatic' } },
              target: 'es2022',
            },
          },
        },
        type: 'javascript/auto',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.jsx', '.js'],
    alias: {
      '@': './src',
    },
  },
  plugins: [
    // Replace `process.env.INMUEBLES_API_URL` at build time so the browser
    // bundle never contains a raw `process` reference (Rspack does not inject
    // Node's `process` into browser bundles by default).
    // Falls back to localhost:8000 when the variable is not set in the env
    // (local development without a .env file).
    new rspack.DefinePlugin({
      'process.env.INMUEBLES_API_URL': JSON.stringify(
        process.env['INMUEBLES_API_URL'] ?? 'http://localhost:8000',
      ),
    }),
    new rspack.HtmlRspackPlugin({
      template: './public/index.html',
    }),
    new ModuleFederationPlugin({
      // Must match the key used in shell's `remotes` config:
      // inmueblesApp: 'inmueblesApp@http://localhost:3001/remoteEntry.js'
      name: 'inmueblesApp',
      filename: 'remoteEntry.js',
      exposes: {
        // Exposed as 'inmueblesApp/PropertyRoutes' — declared in shell's
        // remotes.d.ts and lazy-loaded from task 16+.
        // Task 15.3: placeholder component; real implementation starts task 16.
        './PropertyRoutes': './src/PropertyRoutes.tsx',
      },
      shared: {
        react: { singleton: true, requiredVersion: false },
        'react-dom': { singleton: true, requiredVersion: false },
        'react-router': { singleton: true, requiredVersion: false },
        '@rentame/auth': { singleton: true, requiredVersion: false },
      },
    }),
  ],
  devServer: {
    port: 3001,
    historyApiFallback: true,
    hot: true,
    // Allow cross-origin requests from the shell (port 3000).
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
};

export default config;
