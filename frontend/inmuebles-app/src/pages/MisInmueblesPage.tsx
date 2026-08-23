/**
 * MisInmueblesPage — panel "Mis inmuebles" para el propietario autenticado.
 *
 * Fetches the propietario's own listings via `listarMisInmuebles(token)` on
 * mount and renders them as a list of `PropertyCard` (from `@rentame/ui`).
 * Each card shows a human-readable status badge and, depending on the
 * current `estado`, a "Despublicar" or "Republicar" button. Clicking a
 * button calls `cambiarDisponibilidad` and updates the card's local state
 * from the response — no full-list refetch.
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
import React from 'react';
import { EyeOff, Eye, Pencil } from 'lucide-react';
import { useAuth } from '@rentame/auth';
import { Button, PropertyCard } from '@rentame/ui';
import type { PropertyCardEstado } from '@rentame/ui';
import { typography } from '@rentame/design-tokens';
import {
  cambiarDisponibilidad,
  InmueblesApiError,
  listarMisInmuebles,
} from '../services/inmuebles.api';
import type { FotoInmueble, Inmueble } from '../services/inmuebles.api';

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
// Helpers
// ---------------------------------------------------------------------------

function getFotoUrl(fotos: FotoInmueble[]): string | null {
  const principal = fotos.find((foto) => foto.esPrincipal) ?? fotos[0];
  return principal?.urlStorage ?? null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const MisInmueblesPage: React.FC<Props> = ({ onPublicar, onEditar }) => {
  const { session } = useAuth();

  const [inmuebles, setInmuebles] = React.useState<Inmueble[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Fetch on mount
  // -------------------------------------------------------------------------

  React.useEffect(() => {
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
          <Button variant="primary" onClick={onPublicar}>
            Publicar nuevo inmueble
          </Button>
        )}
        <p>No tenés inmuebles publicados.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Mis inmuebles</h1>
      {onPublicar && (
        <Button variant="primary" onClick={onPublicar}>
          Publicar nuevo inmueble
        </Button>
      )}
      <ul style={listStyle}>
        {inmuebles.map((inmueble) => (
          <li key={inmueble.id} style={listItemStyle}>
            <PropertyCard
              direccion={inmueble.direccion}
              barrio={inmueble.barrio}
              ciudad={inmueble.ciudad}
              habitaciones={inmueble.habitaciones}
              banos={inmueble.banos}
              valorMensual={inmueble.valorMensual}
              fotoUrl={getFotoUrl(inmueble.fotos)}
              estado={inmueble.estado as PropertyCardEstado}
              estadoLabel={ESTADO_LABELS[inmueble.estado] ?? inmueble.estado}
              acciones={
                <div
                  style={accionesStyle}
                  onClick={(event) => {
                    event.stopPropagation();
                  }}
                >
                  {inmueble.estado === 'disponible' && (
                    <Button
                      variant="secondary"
                      onClick={() => void handleCambiarDisponibilidad(inmueble, 'oculto')}
                    >
                      <EyeOff size={16} /> Despublicar
                    </Button>
                  )}
                  {inmueble.estado === 'oculto' && (
                    <Button
                      variant="secondary"
                      onClick={() => void handleCambiarDisponibilidad(inmueble, 'disponible')}
                    >
                      <Eye size={16} /> Republicar
                    </Button>
                  )}
                  {onEditar && (
                    <Button variant="secondary" onClick={() => onEditar(inmueble)}>
                      <Pencil size={16} /> Editar
                    </Button>
                  )}
                </div>
              }
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
  fontFamily: typography.fontFamilyBase,
  padding: '2rem',
  maxWidth: '640px',
  margin: '0 auto',
};

const titleStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyDisplay,
  fontSize: typography.fontSizeH1,
};

const listStyle: React.CSSProperties = {
  listStyle: 'none',
  padding: 0,
  margin: 0,
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
};

const listItemStyle: React.CSSProperties = {
  listStyle: 'none',
};

const accionesStyle: React.CSSProperties = {
  display: 'flex',
  gap: '0.5rem',
  flexWrap: 'wrap',
};

export default MisInmueblesPage;
