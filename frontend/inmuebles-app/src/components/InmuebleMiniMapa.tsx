/**
 * InmuebleMiniMapa — mini mapa Leaflet de un solo punto, para la página de
 * detalle de un inmueble público (mini-mapa-detalle-inmueble).
 *
 * A diferencia de `InmueblesMap` (HU-010, pensado para varios inmuebles a
 * la vez: centro promedio, un marcador por cada uno, popup con "Ver
 * detalle"), este componente centra directamente en las coordenadas dadas
 * y pinta un único marcador sin popup — ya se está en el detalle de ese
 * inmueble, así que no hace falta ninguna acción de navegación.
 *
 * `scrollWheelZoom` está deshabilitado a propósito (design.md decisión 3):
 * este mapa vive embebido dentro de una página que el usuario
 * probablemente está scrolleando de punta a punta, así que el scroll del
 * mouse sobre el mini mapa siempre debe mover la página, nunca hacer zoom.
 * El usuario puede igual hacer zoom con los botones +/- o pellizcando en
 * mobile.
 */
import React from 'react';
import { MapContainer, Marker, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { defaultMarkerIcon } from './leafletIcon';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Más cercano que InmueblesMap.DEFAULT_ZOOM (12, pensado para varios
// inmuebles dispersos por la ciudad) — acá el punto es uno solo y conocido,
// así que conviene mostrar el entorno inmediato (nivel de calle).
const DEFAULT_ZOOM = 16;

const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION = '&copy; OpenStreetMap contributors';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  latitud: number;
  longitud: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const InmuebleMiniMapa: React.FC<Props> = ({ latitud, longitud }) => {
  const center: [number, number] = [latitud, longitud];

  return (
    <div style={containerStyle} data-testid="inmueble-mini-mapa">
      <MapContainer center={center} zoom={DEFAULT_ZOOM} style={mapStyle} scrollWheelZoom={false}>
        <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} />
        <Marker position={center} icon={defaultMarkerIcon} />
      </MapContainer>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '240px',
  borderRadius: '8px',
  overflow: 'hidden',
  marginBottom: '1rem',
};

const mapStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
};

export default InmuebleMiniMapa;
