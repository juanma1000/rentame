/**
 * Standalone dev bootstrap for arrendamiento-app.
 *
 * Only used when the remote runs on its own (npm start, port 3002). In
 * production/integration the shell (or inmuebles-app, cross-remote) lazy-loads
 * ArrendamientoRoutes via MF2 and never executes this file directly.
 *
 * Wraps ArrendamientoRoutes in AuthProvider so the component tree can consume
 * useAuth() even in isolated mode — same pattern as
 * inmuebles-app/src/bootstrap.tsx.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/dm-serif-display';
import '@rentame/design-tokens/src/tokens.css';
import { AuthProvider } from '@rentame/auth';
import ArrendamientoRoutes from './ArrendamientoRoutes';

const container = document.getElementById('root');
if (!container) {
  throw new Error('[rentame-arrendamiento-app] Root element #root not found in DOM.');
}

createRoot(container).render(
  <React.StrictMode>
    <AuthProvider>
      <ArrendamientoRoutes />
    </AuthProvider>
  </React.StrictMode>,
);
