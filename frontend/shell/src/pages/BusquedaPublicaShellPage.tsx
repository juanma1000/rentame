import React, { Suspense } from 'react';

/**
 * Shell wrapper for the "/" public landing route.
 *
 * Lazy-loads the inmuebles-app Module Federation remote, which exposes
 * `BusquedaPublicaRoutes` as its top-level component. That remote owns its
 * own internal listado/detalle state machine — no nested react-router
 * routes are needed here (same lazy-load pattern as `MisInmueblesPage.tsx`,
 * which mounts `inmueblesApp/PropertyRoutes`).
 *
 * This page used to also compose a session-aware header around the remote,
 * but that header is now centralized in `layouts/AppLayout.tsx` (see
 * `openspec/changes/ui-layout-navegacion/design.md`, decisions 1-3), which
 * wraps every route — including this one — at the `App.tsx` level. Keeping
 * a second header here would duplicate it, so this page is now just the
 * `Suspense` boundary around the lazy-loaded remote.
 */

const BusquedaPublicaRoutes = React.lazy(() => import('inmueblesApp/BusquedaPublicaRoutes'));

const BusquedaPublicaShellPage: React.FC = () => (
  <Suspense
    fallback={
      <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
        <p>Cargando inmuebles...</p>
      </main>
    }
  >
    <BusquedaPublicaRoutes />
  </Suspense>
);

export default BusquedaPublicaShellPage;
