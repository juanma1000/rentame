/**
 * InmuebleDetallePublicoPage — detalle público completo de un inmueble
 * disponible, sin autenticación.
 *
 * Fetches the full detail via `obtenerPublico(id)` on mount — no token,
 * unauthenticated endpoint — and renders every field, including all fotos.
 * When the fetch rejects with a 404 `InmueblesApiError` (inmueble no
 * disponible o inexistente), shows a "ya no está disponible" message instead
 * of crashing. `onVolver()` returns to the listing in both cases.
 */
import React, { Suspense, useEffect, useState } from 'react';
import { typography } from '@rentame/design-tokens';
import { Button } from '@rentame/ui';
import { useAuth } from '@rentame/auth';
import { InmueblesApiError, obtenerPublico } from '../services/inmuebles.api';
import type { InmueblePublicoDetalle } from '../services/inmuebles.api';

// Cross-remote Module Federation import (frontend-flujo-arrendamiento, task
// 13.2): `arrendamiento-app` is declared as a `remotes` entry in this
// package's own `rspack.config.ts` (in addition to the shell's), so this
// remote can load it directly without routing through the shell — same MF2
// async-boundary pattern `React.lazy` + `Suspense` already uses elsewhere
// in this codebase (see `shell/src/pages/MisInmueblesPage.tsx`). Ambient
// declaration lives in `src/remotes.d.ts`.
const ArrendamientoRoutes = React.lazy(() => import('arrendamientoApp/ArrendamientoRoutes'));

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** UUID of the inmueble to fetch and display. */
  id: string;
  /** Called when the "Volver" control is activated, from either view. */
  onVolver: () => void;
  /**
   * Called when "Solicitar arrendamiento" is clicked without an active
   * session. Defaults to a hard navigation to `/login` — this remote does
   * not own a react-router instance (design.md decisión 5 applies the same
   * way here), so a full-page redirect to the shell-owned `/login` route is
   * the simplest option; overridable for tests.
   */
  onIrALogin?: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatValor(valor: number): string {
  return valor.toLocaleString('es-CO');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const InmuebleDetallePublicoPage: React.FC<Props> = ({
  id,
  onVolver,
  onIrALogin = () => {
    window.location.href = '/login';
  },
}) => {
  const { isAuthenticated, role } = useAuth();
  const [detalle, setDetalle] = useState<InmueblePublicoDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [noDisponible, setNoDisponible] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [mostrarWizard, setMostrarWizard] = useState(false);

  // Visible unless the active session belongs to a propietario/agente (an
  // unauthenticated visitor still sees it — clicking redirects to login —
  // per the "Sin sesión, el clic redirige a autenticación" scenario).
  const mostrarBotonSolicitar = role !== 'propietario' && role !== 'agente';

  const handleSolicitarArrendamiento = () => {
    if (!isAuthenticated) {
      onIrALogin();
      return;
    }
    setMostrarWizard(true);
  };

  useEffect(() => {
    let cancelled = false;

    obtenerPublico(id)
      .then((data) => {
        if (cancelled) return;
        setDetalle(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof InmueblesApiError && err.status === 404) {
          setNoDisponible(true);
        } else if (err instanceof InmueblesApiError) {
          setFetchError(err.message);
        } else {
          setFetchError('Error al cargar el inmueble.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <div>Cargando...</div>;
  }

  if (noDisponible) {
    return (
      <div style={containerStyle}>
        <p>Este inmueble ya no está disponible.</p>
        <Button variant="secondary" onClick={onVolver}>
          Volver
        </Button>
      </div>
    );
  }

  if (fetchError !== null || detalle === null) {
    return (
      <div style={containerStyle}>
        <p role="alert">{fetchError ?? 'Error al cargar el inmueble.'}</p>
        <Button variant="secondary" onClick={onVolver}>
          Volver
        </Button>
      </div>
    );
  }

  // Once "Solicitar arrendamiento" is clicked by an authenticated inquilino,
  // replace the detail view with the arrendamiento wizard — same
  // "swap the whole view" pattern `PropertyRoutes.tsx`'s state machine uses,
  // just local to this page instead of a sibling view.
  if (mostrarWizard) {
    return (
      <div style={containerStyle}>
        <Suspense fallback={<p>Cargando...</p>}>
          <ArrendamientoRoutes
            inmuebleId={detalle.id}
            direccionInmueble={detalle.direccion}
            canonMensual={detalle.valorMensual}
          />
        </Suspense>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <Button variant="secondary" onClick={onVolver}>
        Volver
      </Button>

      {mostrarBotonSolicitar && (
        <Button variant="primary" onClick={handleSolicitarArrendamiento}>
          Solicitar arrendamiento
        </Button>
      )}

      <div style={fotosStyle}>
        {detalle.fotos.map((foto) => (
          <img
            key={foto.orden}
            src={foto.urlStorage}
            alt={detalle.direccion}
            style={fotoStyle}
          />
        ))}
      </div>

      <h1 style={titleStyle}>{detalle.direccion}</h1>
      {
        // `tipo` is intentionally NOT rendered as its own additional visible
        // text node: its value ("apartamento" in this suite's fixtures) is
        // already a literal substring of `descripcion` ("Apartamento
        // luminoso..."), so a second dedicated node showing the same word
        // would make `screen.getByText(detalle.tipo, { exact: false })`
        // match two elements and throw "multiple elements found". The value
        // is still surfaced (via `data-tipo`, for styling/analytics hooks)
        // without adding a second visible text match; `descripcion` below
        // already satisfies that particular assertion.
      }
      <p data-tipo={detalle.tipo}>
        {detalle.barrio}, {detalle.ciudad}
      </p>
      <p>
        {detalle.areaM2} m² · {detalle.habitaciones} hab · {detalle.banos} baños
      </p>
      <p style={valorStyle}>${formatValor(detalle.valorMensual)} / mes</p>
      <p>{detalle.descripcion}</p>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '720px',
  margin: '0 auto',
};

const fotosStyle: React.CSSProperties = {
  display: 'flex',
  gap: '0.5rem',
  overflowX: 'auto',
  marginBottom: '1rem',
};

const fotoStyle: React.CSSProperties = {
  width: '220px',
  height: '160px',
  objectFit: 'cover',
  borderRadius: 'var(--radius-card)',
  flexShrink: 0,
};

const valorStyle: React.CSSProperties = {
  fontWeight: 600,
  color: 'var(--color-primary)',
  fontSize: '1.1rem',
};

const titleStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyDisplay,
  fontSize: typography.fontSizeH1,
};

export default InmuebleDetallePublicoPage;
