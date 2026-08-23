/**
 * InmueblesGestionadosPage — panel "Inmuebles que gestiono" para el agente
 * autenticado.
 *
 * Fetches the agente's managed listings via `listarInmueblesGestionados(token)`
 * on mount and renders them as a list of `PropertyCard` (from `@rentame/ui`).
 * Each card shows a human-readable status badge and, when `onEditar` is
 * provided, an "Editar" button (same optional pattern as `MisInmueblesPage`).
 * When `onPublicar` is provided, a "Publicar nuevo inmueble" button is
 * rendered — agents can publish on behalf of a property owner per HU-002.
 *
 * Status badge mapping (per `EstadoInmueble` in
 * `backend/inmuebles/domain/inmueble.py`):
 *   - `"disponible"`    → "Disponible"
 *   - `"no_disponible"` → "No disponible"
 *   - `"oculto"`        → "Despublicado"
 */
import React from 'react';
import { Pencil } from 'lucide-react';
import { useAuth } from '@rentame/auth';
import { Button, PropertyCard } from '@rentame/ui';
import type { PropertyCardEstado } from '@rentame/ui';
import { typography } from '@rentame/design-tokens';
import { InmueblesApiError, listarInmueblesGestionados } from '../services/inmuebles.api';
import type { FotoInmueble, Inmueble } from '../services/inmuebles.api';

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
// Helpers
// ---------------------------------------------------------------------------

function getFotoUrl(fotos: FotoInmueble[]): string | null {
  const principal = fotos.find((foto) => foto.esPrincipal) ?? fotos[0];
  return principal?.urlStorage ?? null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const InmueblesGestionadosPage: React.FC<Props> = ({ onPublicar, onEditar }) => {
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
          <Button variant="primary" onClick={onPublicar}>
            Publicar nuevo inmueble
          </Button>
        )}
        <p>No gestionás ningún inmueble.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Inmuebles que gestiono</h1>
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
                onEditar && (
                  <div
                    style={accionesStyle}
                    onClick={(event) => {
                      event.stopPropagation();
                    }}
                  >
                    <Button variant="secondary" onClick={() => onEditar(inmueble)}>
                      <Pencil size={16} /> Editar
                    </Button>
                  </div>
                )
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

export default InmueblesGestionadosPage;
