import { rspack, type Configuration } from '@rspack/core';
import { ModuleFederationPlugin } from '@module-federation/enhanced/rspack';

const isDev = process.env['NODE_ENV'] !== 'production';

const config: Configuration = {
  entry: './src/main.tsx',
  output: {
    // 'auto' lets Rspack infer the public path from the request URL —
    // works for both dev server and static deployments. Same rationale as
    // inmuebles-app/rspack.config.ts (this remote is never served from the
    // domain root, only loaded by the shell via remoteEntry.js).
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
      {
        test: /\.css$/,
        type: 'css',
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
    // Replace `process.env.ARRENDAMIENTO_API_URL` at build time so the
    // browser bundle never contains a raw `process` reference. Falls back
    // to localhost:8000 when the variable is not set (local dev without a
    // .env file) — same convention as INMUEBLES_API_URL.
    new rspack.DefinePlugin({
      'process.env.ARRENDAMIENTO_API_URL': JSON.stringify(
        process.env['ARRENDAMIENTO_API_URL'] ?? 'http://localhost:8000',
      ),
    }),
    new rspack.HtmlRspackPlugin({
      template: './public/index.html',
    }),
    new ModuleFederationPlugin({
      // Must match the key used in shell's (and inmuebles-app's) `remotes`
      // config: arrendamientoApp: 'arrendamientoApp@http://localhost:3002/remoteEntry.js'
      name: 'arrendamientoApp',
      filename: 'remoteEntry.js',
      exposes: {
        // Exposed as 'arrendamientoApp/ArrendamientoRoutes' — top-level
        // route component for the 4-step arrendamiento wizard + "Mi
        // arrendamiento", consumed by both the shell and (cross-remote)
        // by inmuebles-app's InmuebleDetallePublicoPage entry point.
        './ArrendamientoRoutes': './src/ArrendamientoRoutes.tsx',
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
    port: 3002,
    historyApiFallback: true,
    hot: true,
    // Allow cross-origin requests from the shell (port 3000) and from
    // inmuebles-app (port 3001), which consumes this remote cross-remote.
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
};

export default config;
