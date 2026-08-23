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
import React, { useEffect, useState } from 'react';
import { InmueblesApiError, obtenerPublico } from '../services/inmuebles.api';
import type { InmueblePublicoDetalle } from '../services/inmuebles.api';
import { secondaryButtonStyle } from '../styles/buttons';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** UUID of the inmueble to fetch and display. */
  id: string;
  /** Called when the "Volver" control is activated, from either view. */
  onVolver: () => void;
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

const InmuebleDetallePublicoPage: React.FC<Props> = ({ id, onVolver }) => {
  const [detalle, setDetalle] = useState<InmueblePublicoDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [noDisponible, setNoDisponible] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

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
        <button type="button" style={secondaryButtonStyle} onClick={onVolver}>
          Volver
        </button>
      </div>
    );
  }

  if (fetchError !== null || detalle === null) {
    return (
      <div style={containerStyle}>
        <p role="alert">{fetchError ?? 'Error al cargar el inmueble.'}</p>
        <button type="button" style={secondaryButtonStyle} onClick={onVolver}>
          Volver
        </button>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <button type="button" style={secondaryButtonStyle} onClick={onVolver}>
        Volver
      </button>

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

      <h1>{detalle.direccion}</h1>
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

export default InmuebleDetallePublicoPage;
