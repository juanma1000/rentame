import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';
import EntradaPage from './pages/EntradaPage';
import LoginPage from './pages/LoginPage';
import RegistroPage from './pages/RegistroPage';
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
 *  /                     → EntradaPage (pantalla de entrada simétrica por rol)
 *  /login                → LoginPage
 *  /registro/propietario → RegistroPage rol="propietario"
 *  /registro/agente      → RegistroPage rol="agente"
 *  /registro/inquilino   → RegistroPage rol="inquilino"
 *  /mis-inmuebles        → PrivateLayout → MisInmueblesPage (placeholder; the
 *                          inmuebles-app remote is mounted here from task 16+)
 *  *                     → 404 fallback
 *
 * PrivateLayout uses AuthGuard with fallback={<Navigate to="/" replace />}.
 * Unauthenticated visits to any /mis-* route redirect to the entry screen.
 */
const App: React.FC = () => (
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EntradaPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro/propietario" element={<RegistroPage rol="propietario" />} />
        <Route path="/registro/agente" element={<RegistroPage rol="agente" />} />
        <Route path="/registro/inquilino" element={<RegistroPage rol="inquilino" />} />

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
