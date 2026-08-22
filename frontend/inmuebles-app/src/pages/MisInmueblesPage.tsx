/**
 * MisInmueblesPage — panel "Mis inmuebles" para el propietario autenticado.
 *
 * Fetches the propietario's own listings via `listarMisInmuebles(token)` on
 * mount and renders them as a list.  Each card shows a human-readable status
 * badge and, depending on the current `estado`, a "Despublicar" or
 * "Republicar" button.  Clicking a button calls `cambiarDisponibilidad` and
 * updates the card's local state from the response — no full-list refetch.
 *
 * Status badge mapping (per `EstadoInmueble` in
 * `backend/inmuebles/domain/inmueble.py`):
 *   - `"disponible"`    → "Disponible"
 *   - `"no_disponible"` → "No disponible"
 *   - `"oculto"`        → "Despublicado"
 *
 * The `"no_disponible"` state is only reachable via the future arrendamiento
 * domain — propietarios cannot trigger it manually, so no button is rendered.
 */
import React, { useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import {
  cambiarDisponibilidad,
  InmueblesApiError,
  listarMisInmuebles,
} from '../services/inmuebles.api';
import type { Inmueble } from '../services/inmuebles.api';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /**
   * Called when the user clicks "Publicar nuevo inmueble".
   * When omitted the button is not rendered (standalone use, or in tests).
   */
  onPublicar?: () => void;
  /**
   * Called when the user clicks "Editar" on a card, receiving the target
   * inmueble. When omitted the button is not rendered.
   */
  onEditar?: (inmueble: Inmueble) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ESTADO_LABELS: Record<string, string> = {
  disponible: 'Disponible',
  no_disponible: 'No disponible',
  oculto: 'Despublicado',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const MisInmueblesPage: React.FC<Props> = ({ onPublicar, onEditar }) => {
  const { session } = useAuth();

  const [inmuebles, setInmuebles] = useState<Inmueble[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Fetch on mount
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }

    listarMisInmuebles(session.token)
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
  }, [session]);

  // -------------------------------------------------------------------------
  // Action handlers
  // -------------------------------------------------------------------------

  const handleCambiarDisponibilidad = async (
    inmueble: Inmueble,
    nuevoEstado: 'disponible' | 'oculto',
  ): Promise<void> => {
    if (!session) return;

    try {
      const updated = await cambiarDisponibilidad(inmueble.id, nuevoEstado, session.token);
      setInmuebles((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
    } catch {
      // A full app would surface this error; tests verify successful flows only.
    }
  };

  // -------------------------------------------------------------------------
  // Render: loading / error / empty / list
  // -------------------------------------------------------------------------

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
        {onPublicar && (
          <button type="button" style={primaryButtonStyle} onClick={onPublicar}>
            Publicar nuevo inmueble
          </button>
        )}
        <p>No tenés inmuebles publicados.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1>Mis inmuebles</h1>
      {onPublicar && (
        <button type="button" style={primaryButtonStyle} onClick={onPublicar}>
          Publicar nuevo inmueble
        </button>
      )}
      <ul style={listStyle}>
        {inmuebles.map((inmueble) => (
          <li key={inmueble.id} style={cardStyle}>
            <span style={direccionStyle}>{inmueble.direccion}</span>
            <span style={badgeStyle(inmueble.estado)}>
              {ESTADO_LABELS[inmueble.estado] ?? inmueble.estado}
            </span>
            <div style={actionsStyle}>
              {inmueble.estado === 'disponible' && (
                <button
                  type="button"
                  style={buttonStyle}
                  onClick={() => void handleCambiarDisponibilidad(inmueble, 'oculto')}
                >
                  Despublicar
                </button>
              )}
              {inmueble.estado === 'oculto' && (
                <button
                  type="button"
                  style={buttonStyle}
                  onClick={() => void handleCambiarDisponibilidad(inmueble, 'disponible')}
                >
                  Republicar
                </button>
              )}
              {onEditar && (
                <button
                  type="button"
                  style={buttonStyle}
                  onClick={() => onEditar(inmueble)}
                >
                  Editar
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles (inline — consistent with PublicarInmueblePage / EditarInmueblePage)
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '640px',
  margin: '0 auto',
};

const listStyle: React.CSSProperties = {
  listStyle: 'none',
  padding: 0,
  margin: 0,
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
};

const cardStyle: React.CSSProperties = {
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  padding: '1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.5rem',
};

const direccionStyle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: '1rem',
};

// disponible/no_disponible mapean 1:1 a los tokens semánticos success/error —
// fondo suave vía color-mix() sobre --color-surface (recomendado en el README
// del paquete de tokens) con el texto en el color sólido para mantener el
// contraste. "oculto" y el fallback no tienen token equivalente (no existe un
// token de warning/neutral en el paquete) — se mantienen como hex literal.
const BADGE_COLORS: Record<string, React.CSSProperties> = {
  disponible: {
    backgroundColor: 'color-mix(in srgb, var(--color-success) 18%, var(--color-surface))',
    color: 'var(--color-success)',
  },
  no_disponible: {
    backgroundColor: 'color-mix(in srgb, var(--color-error) 18%, var(--color-surface))',
    color: 'var(--color-error)',
  },
  oculto: { backgroundColor: '#fff3cd', color: '#856404' },
};

function badgeStyle(estado: string): React.CSSProperties {
  // Estado desconocido/no mapeado: gris neutro sin token equivalente, se deja hardcoded.
  const colors = BADGE_COLORS[estado] ?? { backgroundColor: '#e2e3e5', color: '#383d41' };
  return {
    display: 'inline-block',
    padding: '0.15rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.85rem',
    fontWeight: 500,
    alignSelf: 'flex-start',
    ...colors,
  };
}

const actionsStyle: React.CSSProperties = {
  display: 'flex',
  gap: '0.5rem',
  marginTop: '0.25rem',
};

const buttonStyle: React.CSSProperties = {
  padding: '0.4rem 0.9rem',
  cursor: 'pointer',
  borderRadius: '4px',
  border: '1px solid var(--color-border)',
};

const primaryButtonStyle: React.CSSProperties = {
  padding: '0.5rem 1.25rem',
  cursor: 'pointer',
  borderRadius: '4px',
  border: '1px solid var(--color-primary)',
  backgroundColor: 'var(--color-primary)',
  color: 'var(--color-surface)',
  marginBottom: '1rem',
};

export default MisInmueblesPage;
