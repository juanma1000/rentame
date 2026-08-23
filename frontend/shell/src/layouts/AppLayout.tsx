import React from 'react';
import { Link, Outlet } from 'react-router';
import { useAuth } from '@rentame/auth';

/**
 * Shared application layout, mounted once at the root of the route tree
 * (see `App.tsx`) and wrapping every route via `<Outlet/>`.
 *
 * Centralizes the session-aware navigation header that previously lived
 * duplicated inside `BusquedaPublicaShellPage` (see
 * `openspec/changes/ui-layout-navegacion/design.md`, decisions 1-3):
 *   - No active session: "Inicio" (`/`), "Publicar mi inmueble"
 *     (`/publicar`), "Iniciar sesión" (`/login`).
 *   - Active session: "Inicio" (`/`), "Mis inmuebles" (`/mis-inmuebles`),
 *     "Cerrar sesión" (calls `useAuth().logout()`). "Publicar mi inmueble"
 *     is fully replaced by "Mis inmuebles" — it does not coexist with
 *     `/publicar` while there is a session.
 *
 * Also renders a persistent footer with the "Rentame" brand text.
 */
const AppLayout: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <div>
      <header
        style={{
          fontFamily: 'sans-serif',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '1rem',
        }}
      >
        <Link to="/">Inicio</Link>
        {isAuthenticated ? (
          <>
            <Link to="/mis-inmuebles">Mis inmuebles</Link>
            <button type="button" onClick={() => logout()}>
              Cerrar sesión
            </button>
          </>
        ) : (
          <>
            <Link to="/publicar">Publicar mi inmueble</Link>
            <Link to="/login">Iniciar sesión</Link>
          </>
        )}
      </header>
      <Outlet />
      <footer style={{ fontFamily: 'sans-serif', padding: '1rem 2rem', textAlign: 'center', color: '#666' }}>
        <p>Rentame</p>
      </footer>
    </div>
  );
};

export default AppLayout;
