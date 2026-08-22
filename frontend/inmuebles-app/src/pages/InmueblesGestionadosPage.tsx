/**
 * InmueblesGestionadosPage — panel "Inmuebles que gestiono" para el agente
 * autenticado.
 *
 * Fetches the agente's managed listings via `listarInmueblesGestionados(token)`
 * on mount and renders them as a list.  Each card shows a human-readable status
 * badge and, when `onEditar` is provided, an "Editar" button (same optional
 * pattern as MisInmueblesPage).  When `onPublicar` is provided, a "Publicar
 * nuevo inmueble" button is rendered — agents can publish on behalf of a
 * property owner per HU-002.
 *
 * Status badge mapping (per `EstadoInmueble` in
 * `backend/inmuebles/domain/inmueble.py`):
 *   - `"disponible"`    → "Disponible"
 *   - `"no_disponible"` → "No disponible"
 *   - `"oculto"`        → "Despublicado"
 */
import React, { useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { InmueblesApiError, listarInmueblesGestionados } from '../services/inmuebles.api';
import type { Inmueble } from '../services/inmuebles.api';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /**
   * Called when the user clicks "Publicar nuevo inmueble".
   * When omitted the button is not rendered.
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

const InmueblesGestionadosPage: React.FC<Props> = ({ onPublicar, onEditar }) => {
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

    listarInmueblesGestionados(session.token)
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
        <p>No gestionás ningún inmueble.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1>Inmuebles que gestiono</h1>
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
            {onEditar && (
              <div style={actionsStyle}>
                <button
                  type="button"
                  style={buttonStyle}
                  onClick={() => onEditar(inmueble)}
                >
                  Editar
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles (inline — consistent with MisInmueblesPage)
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

export default InmueblesGestionadosPage;
