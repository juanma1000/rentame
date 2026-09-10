/**
 * InmueblesMap — Leaflet/OpenStreetMap view of the public listing
 * (vista-mapa-inmuebles-leaflet), rendered by `BusquedaPublicaPage` as an
 * alternative to the list view via a Lista/Mapa toggle.
 *
 * Only inmuebles with non-null `latitud`/`longitud` get a marker — an
 * inmueble without coordinates (geocoding never ran, or found nothing) is
 * silently omitted, never an error (spec.md: "Marcadores de inmuebles en el
 * mapa"). Clicking a marker opens a popup with its foto principal, valor
 * mensual and an action to navigate to its detail — same `onVerDetalle(id)`
 * callback `BusquedaPublicaPage` already threads through to the list view's
 * cards, so this component stays router-agnostic like the rest of this
 * microfrontend (design.md decision 5 of hu-003).
 */
import React from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import { colors, spacing, typography } from '@rentame/design-tokens';
import type { InmueblePublico } from '../services/inmuebles.api';
import 'leaflet/dist/leaflet.css';
import { defaultMarkerIcon } from './leafletIcon';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Default map center when no inmueble has coordinates (design.md: Medellín). */
const MEDELLIN_CENTER: [number, number] = [6.244203, -75.581212];
const DEFAULT_ZOOM = 12;

const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '&copy; OpenStreetMap contributors';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  inmuebles: InmueblePublico[];
  onVerDetalle: (id: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface InmuebleConCoordenadas extends InmueblePublico {
  latitud: number;
  longitud: number;
}

function tieneCoordenadas(inmueble: InmueblePublico): inmueble is InmuebleConCoordenadas {
  return inmueble.latitud !== null && inmueble.longitud !== null;
}

/** Center on the average of every inmueble with coordinates, or Medellín
 * when none has any — same rationale `PropertyCard` uses for a null foto:
 * degrade gracefully instead of erroring. */
function calcularCentro(inmuebles: InmuebleConCoordenadas[]): [number, number] {
  if (inmuebles.length === 0) {
    return MEDELLIN_CENTER;
  }
  const sumaLat = inmuebles.reduce((acc, inmueble) => acc + inmueble.latitud, 0);
  const sumaLng = inmuebles.reduce((acc, inmueble) => acc + inmueble.longitud, 0);
  return [sumaLat / inmuebles.length, sumaLng / inmuebles.length];
}

function formatValor(valor: number): string {
  return `$${valor.toLocaleString('es-CO')}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const InmueblesMap: React.FC<Props> = ({ inmuebles, onVerDetalle }) => {
  const conCoordenadas = inmuebles.filter(tieneCoordenadas);
  const center = calcularCentro(conCoordenadas);

  return (
    <div style={containerStyle} data-testid="inmuebles-map">
      <MapContainer
        center={center}
        zoom={DEFAULT_ZOOM}
        style={mapStyle}
        scrollWheelZoom
      >
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        {conCoordenadas.map((inmueble) => (
          <Marker
            key={inmueble.id}
            position={[inmueble.latitud, inmueble.longitud]}
            icon={defaultMarkerIcon}
          >
            <Popup>
              <div style={popupStyle}>
                {inmueble.fotoPrincipal && (
                  <img
                    src={inmueble.fotoPrincipal}
                    alt={inmueble.direccion}
                    style={popupImgStyle}
                  />
                )}
                <p style={popupValorStyle}>{formatValor(inmueble.valorMensual)}</p>
                <button
                  type="button"
                  style={popupButtonStyle}
                  onClick={() => onVerDetalle(inmueble.id)}
                >
                  Ver detalle
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '520px',
  borderRadius: '8px',
  overflow: 'hidden',
};

const mapStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
};

const popupStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyBase,
  minWidth: '160px',
};

const popupImgStyle: React.CSSProperties = {
  width: '100%',
  height: '100px',
  objectFit: 'cover',
  borderRadius: '4px',
  marginBottom: spacing[2],
};

const popupValorStyle: React.CSSProperties = {
  margin: `0 0 ${spacing[2]}`,
  fontWeight: typography.fontWeightBold,
  color: colors.primary,
};

const popupButtonStyle: React.CSSProperties = {
  border: 'none',
  backgroundColor: colors.primary,
  color: colors.surface,
  borderRadius: '4px',
  padding: `${spacing[1]} ${spacing[2]}`,
  cursor: 'pointer',
  width: '100%',
};

export default InmueblesMap;
