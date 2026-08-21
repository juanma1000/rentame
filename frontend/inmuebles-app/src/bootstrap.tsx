/**
 * Standalone dev bootstrap for inmuebles-app.
 *
 * Only used when the remote runs on its own (npm start, port 3001).
 * In production/integration the shell lazy-loads PropertyRoutes via MF2
 * and never executes this file directly.
 *
 * Wraps PropertyRoutes in AuthProvider so the component tree can consume
 * useAuth() even in isolated mode.  The dev workflow is: paste a JWT via
 * TokenLoginPage on the shell, or set RENTAME_DEV_TOKEN in the environment
 * for scripted dev sessions (documented in frontend/README.md).
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { AuthProvider } from '@rentame/auth';
import PropertyRoutes from './PropertyRoutes';

const container = document.getElementById('root');
if (!container) {
  throw new Error('[rentame-inmuebles-app] Root element #root not found in DOM.');
}

createRoot(container).render(
  <React.StrictMode>
    <AuthProvider>
      <PropertyRoutes />
    </AuthProvider>
  </React.StrictMode>,
);
