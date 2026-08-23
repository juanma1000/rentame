import React, { Suspense } from 'react';
import { Link } from 'react-router';

/**
 * Shell wrapper for the "/" public landing route.
 *
 * Composes a lightweight header (with links to "Publicar mi inmueble" and
 * "Iniciar sesión") around the lazy-loaded inmuebles-app Module Federation
 * remote, which exposes `BusquedaPublicaRoutes` as its top-level component.
 * That remote owns its own internal listado/detalle state machine — no
 * nested react-router routes are needed here (same lazy-load pattern as
 * `MisInmueblesPage.tsx`, which mounts `inmueblesApp/PropertyRoutes`).
 */

const BusquedaPublicaRoutes = React.lazy(() => import('inmueblesApp/BusquedaPublicaRoutes'));

const BusquedaPublicaShellPage: React.FC = () => (
  <div>
    <header style={{ fontFamily: 'sans-serif', padding: '1rem 2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
      <Link to="/publicar">Publicar mi inmueble</Link>
      <Link to="/login">Iniciar sesión</Link>
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

export default BusquedaPublicaShellPage;
