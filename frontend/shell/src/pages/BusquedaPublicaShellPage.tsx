import React, { Suspense, useContext } from 'react';
import { Link } from 'react-router';
import { AuthContext } from '@rentame/auth';

/**
 * Shell wrapper for the "/" public landing route.
 *
 * Composes a lightweight, session-aware header around the lazy-loaded
 * inmuebles-app Module Federation remote, which exposes
 * `BusquedaPublicaRoutes` as its top-level component. That remote owns its
 * own internal listado/detalle state machine — no nested react-router
 * routes are needed here (same lazy-load pattern as `MisInmueblesPage.tsx`,
 * which mounts `inmueblesApp/PropertyRoutes`).
 *
 * Header behavior:
 *   - No active session: "Publicar mi inmueble" → `/publicar`, plus
 *     "Iniciar sesión" → `/login`.
 *   - Active session: "Publicar mi inmueble" → `/mis-inmuebles`, plus a
 *     "Mis inmuebles" link → `/mis-inmuebles` and a "Cerrar sesión" button
 *     that calls `logout()`. No "Iniciar sesión" link.
 *
 * Reads auth state via `useContext(AuthContext)` directly (rather than
 * `useAuth()`) so this page still renders its unauthenticated header when
 * mounted outside an `AuthProvider` — `useAuth()` throws in that case. In
 * production this page is always mounted under the shell's app-level
 * `AuthProvider` (see `App.tsx`), so the fallback only matters for tests
 * that render it standalone.
 */

const BusquedaPublicaRoutes = React.lazy(() => import('inmueblesApp/BusquedaPublicaRoutes'));

const BusquedaPublicaShellPage: React.FC = () => {
  const auth = useContext(AuthContext);
  const isAuthenticated = auth?.isAuthenticated ?? false;
  const logout = auth?.logout;

  return (
    <div>
      <header style={{ fontFamily: 'sans-serif', padding: '1rem 2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
        <Link to={isAuthenticated ? '/mis-inmuebles' : '/publicar'}>Publicar mi inmueble</Link>
        {isAuthenticated ? (
          <>
            <Link to="/mis-inmuebles">Mis inmuebles</Link>
            <button type="button" onClick={() => logout?.()}>
              Cerrar sesión
            </button>
          </>
        ) : (
          <Link to="/login">Iniciar sesión</Link>
        )}
      </header>
      <Suspense
        fallback={
          <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
            <p>Cargando inmuebles...</p>
          </main>
        }
      >
        <BusquedaPublicaRoutes />
      </Suspense>
    </div>
  );
};

export default BusquedaPublicaShellPage;
