import React, { useState } from 'react';
import BusquedaPublicaPage from './pages/BusquedaPublicaPage';
import InmuebleDetallePublicoPage from './pages/InmuebleDetallePublicoPage';

/**
 * BusquedaPublicaRoutes — top-level route component exposed by the
 * inmuebles-app remote via Module Federation for the public (unauthenticated)
 * listing/detail flow.
 *
 * Navigation model: local state machine (no nested react-router), same
 * pattern as `PropertyRoutes.tsx` — the shell already owns the URL for the
 * whole app.
 *
 * Views:
 *   listado  — BusquedaPublicaPage (default).
 *   detalle  — InmuebleDetallePublicoPage, receiving the selected id as a
 *              prop. `onVolver` returns to the listado view.
 *
 * Consumed by the shell via:
 *   const BusquedaPublicaRoutes = React.lazy(() => import('inmueblesApp/BusquedaPublicaRoutes'))
 */

// ---------------------------------------------------------------------------
// State machine types
// ---------------------------------------------------------------------------

type View = { kind: 'listado' } | { kind: 'detalle'; id: string };

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const BusquedaPublicaRoutes: React.FC = () => {
  const [view, setView] = useState<View>({ kind: 'listado' });

  const goToDetalle = (id: string) => setView({ kind: 'detalle', id });
  const volverAListado = () => setView({ kind: 'listado' });

  return (
    <div data-testid="busqueda-publica-routes">
      {view.kind === 'listado' && <BusquedaPublicaPage onVerDetalle={goToDetalle} />}

      {view.kind === 'detalle' && (
        <InmuebleDetallePublicoPage id={view.id} onVolver={volverAListado} />
      )}
    </div>
  );
};

export default BusquedaPublicaRoutes;
