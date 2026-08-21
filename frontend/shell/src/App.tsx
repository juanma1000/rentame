import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';
import TokenLoginPage from './pages/TokenLoginPage';
import PrivateLayout from './layouts/PrivateLayout';
import MisInmueblesPage from './pages/MisInmueblesPage';

/**
 * Shell application root.
 *
 * AuthProvider wraps the entire tree so the auth context (session, role,
 * login/logout) is available to every route, layout and lazy-loaded remote.
 *
 * Route structure
 * ────────────────
 *  /               → TokenLoginPage (dev-time JWT entry point; replaced by a
 *                    real login flow when the `usuarios` domain has a UI)
 *  /mis-inmuebles  → PrivateLayout → MisInmueblesPage (placeholder; the
 *                    inmuebles-app remote is mounted here from task 16+)
 *  *               → 404 fallback
 *
 * PrivateLayout uses AuthGuard with fallback={<Navigate to="/" replace />}.
 * Unauthenticated visits to any /mis-* route redirect to the login entry.
 */
const App: React.FC = () => (
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        {/*
         * DEV ONLY: TokenLoginPage lets the developer paste a JWT manually to
         * initialise a session without a real login UI.  Replaced by a real
         * auth flow once the `usuarios` domain has a UI (out of scope HU-001).
         */}
        <Route path="/" element={<TokenLoginPage />} />

        {/* Protected routes — require an active session via PrivateLayout */}
        <Route element={<PrivateLayout />}>
          {/*
           * /mis-inmuebles: placeholder for the inmuebles-app MFE remote.
           * Real content is lazy-loaded via Module Federation from task 16+.
           */}
          <Route path="/mis-inmuebles" element={<MisInmueblesPage />} />
        </Route>

        <Route
          path="*"
          element={
            <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
              <h2>Rentame</h2>
              <p>Ruta no encontrada.</p>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
);

export default App;
