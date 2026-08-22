import { rspack, type Configuration } from '@rspack/core';
import { ModuleFederationPlugin } from '@module-federation/enhanced/rspack';

const isDev = process.env['NODE_ENV'] !== 'production';

const config: Configuration = {
  entry: './src/main.tsx',
  output: {
    // Absolute, not 'auto': nginx's SPA fallback serves index.html for
    // every client-side route (e.g. /registro/agente), and 'auto' resolves
    // the script src relative to that URL (-> /registro/main.js, 404 ->
    // index.html served as JS -> "Unexpected token '<'"). Shell is always
    // served from the domain root, so '/' is correct in every deployment.
    publicPath: '/',
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
    new rspack.DefinePlugin({
      'process.env.USUARIOS_API_URL': JSON.stringify(
        process.env['USUARIOS_API_URL'] ?? 'http://localhost:8000',
      ),
    }),
    new rspack.HtmlRspackPlugin({
      template: './public/index.html',
    }),
    new ModuleFederationPlugin({
      name: 'shell',
      remotes: {
        // inmuebles-app remote — bootstrapped in task 15+, served on port 3001.
        // The URL intentionally points to a server that does not exist yet;
        // the remote will be available once feature/hu-001-inmuebles-app is
        // bootstrapped and running.  Module Federation 2.0 will fail gracefully
        // (runtime error on the first navigation that tries to load the remote)
        // rather than crashing the whole shell on startup.
        inmueblesApp: 'inmueblesApp@http://localhost:3001/remoteEntry.js',
      },
      shared: {
        react: { singleton: true, requiredVersion: false },
        'react-dom': { singleton: true, requiredVersion: false },
        'react-router': { singleton: true, requiredVersion: false },
        '@rentame/auth': { singleton: true },
      },
    }),
  ],
  devServer: {
    port: 3000,
    historyApiFallback: true,
    hot: true,
  },
};

export default config;
