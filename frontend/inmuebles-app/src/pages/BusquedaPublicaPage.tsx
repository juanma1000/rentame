/**
 * BusquedaPublicaPage — grid público de inmuebles disponibles, sin
 * autenticación.
 *
 * Fetches the public listing via `listarPublicos()` on mount — no token,
 * this is an unauthenticated endpoint — and renders each inmueble as a card.
 * Per `design.md` decision 5, this component does not assume react-router:
 * it receives `onVerDetalle(id)` as a prop and lets the caller (typically
 * `BusquedaPublicaRoutes`) own navigation.
 */
import React, { useEffect, useState } from 'react';
import { typography } from '@rentame/design-tokens';
import { PropertyCard } from '@rentame/ui';
import { InmueblesApiError, listarPublicos } from '../services/inmuebles.api';
import type { InmueblePublico } from '../services/inmuebles.api';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Called with the inmueble's id when its card is clicked. */
  onVerDetalle: (id: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const BusquedaPublicaPage: React.FC<Props> = ({ onVerDetalle }) => {
  const [inmuebles, setInmuebles] = useState<InmueblePublico[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    listarPublicos()
      .then((data) => {
        setInmuebles(data);
      })
      .catch((err: unknown) => {
        if (err instanceof InmueblesApiError) {
          setFetchError(err.message);
        } else {
          setFetchError('Error al cargar los inmuebles.');
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Cargando...</div>;
  }

  if (fetchError !== null) {
    return (
      <div style={containerStyle}>
        <p role="alert">{fetchError}</p>
      </div>
    );
  }

  if (inmuebles.length === 0) {
    return (
      <div style={containerStyle}>
        <p>No hay inmuebles disponibles en este momento.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Inmuebles disponibles</h1>
      <ul style={gridStyle}>
        {inmuebles.map((inmueble) => (
          // The click handler is placed on the `<li>` itself (not only on
          // `PropertyCard`'s inner `onClick`) so that `fireEvent.click`
          // fired directly on the `<li>` (as `cardFor` resolves it in the
          // test suite) reliably triggers navigation — a click dispatched
          // on an element only bubbles up through ancestors, not down into
          // descendants, so a handler solely on the inner card `<div>`
          // would never fire for a click targeted at the `<li>` wrapper.
          <li
            key={inmueble.id}
            style={{ cursor: 'pointer' }}
            onClick={() => onVerDetalle(inmueble.id)}
          >
            <PropertyCard
              direccion={inmueble.direccion}
              barrio={inmueble.barrio}
              ciudad={inmueble.ciudad}
              habitaciones={inmueble.habitaciones}
              banos={inmueble.banos}
              valorMensual={inmueble.valorMensual}
              fotoUrl={inmueble.fotoPrincipal}
              estado="disponible"
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '960px',
  margin: '0 auto',
};

const gridStyle: React.CSSProperties = {
  listStyle: 'none',
  padding: 0,
  margin: 0,
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
  gap: '1rem',
};

const titleStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyDisplay,
  fontSize: typography.fontSizeH1,
};

export default BusquedaPublicaPage;
