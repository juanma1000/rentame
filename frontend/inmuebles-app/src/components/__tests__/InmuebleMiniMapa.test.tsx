/**
 * Unit tests for `InmuebleMiniMapa` (mini-mapa-detalle-inmueble).
 *
 * `react-leaflet` is mocked entirely — same rationale as
 * `InmueblesMap.test.tsx`: real Leaflet map rendering needs real DOM
 * layout jsdom doesn't provide, and isn't this component's own logic.
 * What IS this component's logic, and what these tests assert:
 *
 *   - it centers on and marks the single point it's given (no averaging,
 *     unlike `InmueblesMap`, which handles multiple inmuebles);
 *   - `scrollWheelZoom` is disabled (spec.md: "Mini mapa en el detalle del
 *     inmueble" — scroll must move the page, never zoom the map);
 *   - the default zoom is closer (street-level) than `InmueblesMap`'s.
 */
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';
import InmuebleMiniMapa from '../InmuebleMiniMapa';

jest.mock('react-leaflet', () => ({
  __esModule: true,
  MapContainer: ({
    children,
    center,
    zoom,
    scrollWheelZoom,
  }: {
    children: React.ReactNode;
    center: [number, number];
    zoom: number;
    scrollWheelZoom: boolean;
  }) => (
    <div
      data-testid="map-container"
      data-center={JSON.stringify(center)}
      data-zoom={zoom}
      data-scroll-wheel-zoom={String(scrollWheelZoom)}
    >
      {children}
    </div>
  ),
  TileLayer: ({ url }: { url: string }) => <div data-testid="tile-layer" data-url={url} />,
  Marker: ({ position }: { position: [number, number] }) => (
    <div data-testid="marker" data-position={JSON.stringify(position)} />
  ),
}));

describe('InmuebleMiniMapa', () => {
  it('centers the map on the given coordinates and renders a single marker there', () => {
    render(<InmuebleMiniMapa latitud={6.244203} longitud={-75.581212} />);

    expect(screen.getByTestId('map-container')).toHaveAttribute(
      'data-center',
      JSON.stringify([6.244203, -75.581212]),
    );
    expect(screen.getAllByTestId('marker')).toHaveLength(1);
    expect(screen.getByTestId('marker')).toHaveAttribute(
      'data-position',
      JSON.stringify([6.244203, -75.581212]),
    );
  });

  it('disables scrollWheelZoom so the mouse wheel always scrolls the page, never zooms the map', () => {
    render(<InmuebleMiniMapa latitud={6.244203} longitud={-75.581212} />);

    expect(screen.getByTestId('map-container')).toHaveAttribute(
      'data-scroll-wheel-zoom',
      'false',
    );
  });

  it('uses a closer default zoom (street-level) than the aggregate InmueblesMap', () => {
    render(<InmuebleMiniMapa latitud={6.244203} longitud={-75.581212} />);

    const zoom = Number(screen.getByTestId('map-container').getAttribute('data-zoom'));
    // InmueblesMap.DEFAULT_ZOOM is 12 (city-wide, many scattered inmuebles).
    expect(zoom).toBeGreaterThan(12);
  });
});
