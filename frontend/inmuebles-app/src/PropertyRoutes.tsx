import React, { useState } from 'react';
import { useAuth } from '@rentame/auth';
import MisInmueblesPage from './pages/MisInmueblesPage';
import InmueblesGestionadosPage from './pages/InmueblesGestionadosPage';
import PublicarInmueblePage from './pages/PublicarInmueblePage';
import EditarInmueblePage from './pages/EditarInmueblePage';
import type { Inmueble } from './services/inmuebles.api';

/**
 * PropertyRoutes — top-level route component exposed by the inmuebles-app
 * remote via Module Federation.
 *
 * Navigation model: local state machine (no nested react-router).
 * The shell already owns the URL; this remote manages its own internal views
 * via `useState` to avoid the complexity of nesting two Router instances.
 *
 * Views:
 *   lista    — MisInmueblesPage (default). Holds a `refreshKey` that
 *              increments after a successful publish or edit, forcing a
 *              remount (and therefore a fresh fetch) of MisInmueblesPage.
 *   publicar — PublicarInmueblePage.
 *   editar   — EditarInmueblePage, receiving the pre-selected Inmueble as a
 *              prop (no route-param + fetch — see EditarInmueblePage contract).
 *
 * Consumed by the shell via:
 *   const PropertyRoutes = React.lazy(() => import('inmueblesApp/PropertyRoutes'))
 */

// ---------------------------------------------------------------------------
// State machine types
// ---------------------------------------------------------------------------

type View =
  | { kind: 'lista'; refreshKey: number }
  | { kind: 'publicar' }
  | { kind: 'editar'; inmueble: Inmueble };

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const PropertyRoutes: React.FC = () => {
  const { role } = useAuth();
  const [view, setView] = useState<View>({ kind: 'lista', refreshKey: 0 });

  // ── Transitions ──────────────────────────────────────────────────────────

  const goToPublicar = () => setView({ kind: 'publicar' });

  const goToEditar = (inmueble: Inmueble) => setView({ kind: 'editar', inmueble });

  /** Return to the lista view, optionally bumping the refreshKey so that
   * MisInmueblesPage remounts and re-fetches the list (used after a
   * successful publish or edit). */
  const volverALista = (shouldRefresh: boolean) =>
    setView((prev) => ({
      kind: 'lista',
      refreshKey: shouldRefresh
        ? (prev.kind === 'lista' ? prev.refreshKey + 1 : 1)
        : prev.kind === 'lista'
          ? prev.refreshKey
          : 0,
    }));

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div data-testid="inmuebles-routes">
      {view.kind === 'lista' && role === 'propietario' && (
        <MisInmueblesPage
          key={view.refreshKey}
          onPublicar={goToPublicar}
          onEditar={goToEditar}
        />
      )}

      {view.kind === 'lista' && role === 'agente' && (
        <InmueblesGestionadosPage
          key={view.refreshKey}
          onPublicar={goToPublicar}
          onEditar={goToEditar}
        />
      )}

      {view.kind === 'publicar' && (
        <PublicarInmueblePage
          onVolver={() => volverALista(false)}
          onPublicado={() => volverALista(true)}
        />
      )}

      {view.kind === 'editar' && (
        <EditarInmueblePage
          inmueble={view.inmueble}
          onVolver={() => volverALista(false)}
          onActualizado={() => volverALista(true)}
        />
      )}
    </div>
  );
};

export default PropertyRoutes;
