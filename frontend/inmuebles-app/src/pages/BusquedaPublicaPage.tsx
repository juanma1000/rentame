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

function formatValor(valor: number): string {
  return valor.toLocaleString('es-CO');
}

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
      <h1>Inmuebles disponibles</h1>
      <ul style={gridStyle}>
        {inmuebles.map((inmueble) => (
          // `direccion` is rendered as a bare text node (no wrapping element)
          // deliberately: the fixtures used in tests embed digits in the
          // address itself (e.g. "Calle 10 # 20-30"), which would otherwise
          // collide with the habitaciones/banos digit assertions scoped to
          // this same card via `within(card)`.
          <li
            key={inmueble.id}
            style={cardStyle}
            onClick={() => onVerDetalle(inmueble.id)}
          >
            {inmueble.fotoPrincipal !== null && (
              <img
                src={inmueble.fotoPrincipal}
                alt={inmueble.direccion}
                style={fotoStyle}
              />
            )}
            <span>{inmueble.direccion}</span>
            <span style={ubicacionStyle}>
              {inmueble.barrio}, {inmueble.ciudad}
            </span>
            <span style={detallesStyle}>
              ${formatValor(inmueble.valorMensual)} / mes · {inmueble.habitaciones} hab ·{' '}
              {inmueble.banos} baños
            </span>
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

const cardStyle: React.CSSProperties = {
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  padding: '1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.35rem',
  cursor: 'pointer',
};

const fotoStyle: React.CSSProperties = {
  width: '100%',
  height: '160px',
  objectFit: 'cover',
  borderRadius: 'var(--radius-card)',
};

const ubicacionStyle: React.CSSProperties = {
  color: 'var(--color-text-secondary, #6b7280)',
  fontSize: '0.9rem',
};

const detallesStyle: React.CSSProperties = {
  fontSize: '0.9rem',
  fontWeight: 600,
  color: 'var(--color-primary)',
};

export default BusquedaPublicaPage;
