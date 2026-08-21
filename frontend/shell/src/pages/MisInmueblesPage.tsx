import React, { Suspense } from 'react';

/**
 * Shell wrapper for the /mis-inmuebles protected route.
 *
 * Lazy-loads the inmuebles-app Module Federation remote and renders it inside
 * a Suspense boundary with a lightweight fallback.  The remote exposes
 * `PropertyRoutes` as its top-level navigation component, which handles the
 * full lista / publicar / editar state machine without requiring nested
 * react-router routes inside the remote.
 *
 * This replaces the static placeholder added in task 14.4 (feature/hu-001-shell).
 */

const PropertyRoutes = React.lazy(() => import('inmueblesApp/PropertyRoutes'));

const MisInmueblesPage: React.FC = () => (
  <Suspense
    fallback={
      <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
        <p>Cargando inmuebles...</p>
      </main>
    }
  >
    <PropertyRoutes />
  </Suspense>
);

export default MisInmueblesPage;
