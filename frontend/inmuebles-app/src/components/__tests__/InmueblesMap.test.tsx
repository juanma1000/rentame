/**
 * Unit tests for `InmueblesMap` (vista-mapa-inmuebles-leaflet).
 *
 * `react-leaflet` is mocked entirely — real Leaflet map rendering needs
 * real DOM layout (tile loading, panes, container sizing) that jsdom
 * doesn't provide, and isn't this component's own logic to verify. What IS
 * this component's logic, and what these tests assert instead:
 *
 *   - which inmuebles get a marker (only those with non-null coordinates);
 *   - what center is computed and handed to `MapContainer`;
 *   - what each marker's popup renders (foto, valor, "Ver detalle" action).
 *
 * `spec.md` requirements covered: "Marcadores de inmuebles en el mapa",
 * "Centrado por defecto del mapa", "Navegación al detalle desde un
 * marcador".
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import type { InmueblePublico } from '../../services/inmuebles.api';
import InmueblesMap from '../InmueblesMap';

// ---------------------------------------------------------------------------
// Mock react-leaflet — see module docstring above.
// ---------------------------------------------------------------------------

jest.mock('react-leaflet', () => ({
  __esModule: true,
  MapContainer: ({
    children,
    center,
    zoom,
  }: {
    children: React.ReactNode;
    center: [number, number];
    zoom: number;
  }) => (
    <div data-testid="map-container" data-center={JSON.stringify(center)} data-zoom={zoom}>
      {children}
    </div>
  ),
  TileLayer: ({ url }: { url: string }) => <div data-testid="tile-layer" data-url={url} />,
  Marker: ({
    children,
    position,
  }: {
    children: React.ReactNode;
    position: [number, number];
  }) => (
    <div data-testid="marker" data-position={JSON.stringify(position)}>
      {children}
    </div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popup">{children}</div>
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeInmueble(overrides: Partial<InmueblePublico>): InmueblePublico {
  return {
    id: 'inmueble-uuid-1',
    fotoPrincipal: 'https://storage.local/foto-1.jpg',
    direccion: 'Calle 10 # 20-30',
    barrio: 'Laureles',
    ciudad: 'Medellín',
    valorMensual: 1_500_000,
    habitaciones: 2,
    banos: 1,
    latitud: 6.244203,
    longitud: -75.581212,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------

describe('InmueblesMap', () => {
  it('renders a marker only for inmuebles with non-null coordinates', () => {
    const conCoordenadas = makeInmueble({ id: 'con-coordenadas' });
    const sinCoordenadas = makeInmueble({
      id: 'sin-coordenadas',
      latitud: null,
      longitud: null,
    });

    render(
      <InmueblesMap inmuebles={[conCoordenadas, sinCoordenadas]} onVerDetalle={jest.fn()} />,
    );

    expect(screen.getAllByTestId('marker')).toHaveLength(1);
    expect(screen.getByTestId('marker')).toHaveAttribute(
      'data-position',
      JSON.stringify([conCoordenadas.latitud, conCoordenadas.longitud]),
    );
  });

  it('renders an empty map, without error, when no inmueble has coordinates', () => {
    const sinCoordenadas = makeInmueble({ latitud: null, longitud: null });

    expect(() =>
      render(<InmueblesMap inmuebles={[sinCoordenadas]} onVerDetalle={jest.fn()} />),
    ).not.toThrow();

    expect(screen.getByTestId('map-container')).toBeInTheDocument();
    expect(screen.queryByTestId('marker')).not.toBeInTheDocument();
  });

  it('centers on Medellín when no inmueble has coordinates', () => {
    const sinCoordenadas = makeInmueble({ latitud: null, longitud: null });

    render(<InmueblesMap inmuebles={[sinCoordenadas]} onVerDetalle={jest.fn()} />);

    expect(screen.getByTestId('map-container')).toHaveAttribute(
      'data-center',
      JSON.stringify([6.244203, -75.581212]),
    );
  });

  it('centers on the average of every inmueble with coordinates', () => {
    const uno = makeInmueble({ id: 'uno', latitud: 6.0, longitud: -75.0 });
    const dos = makeInmueble({ id: 'dos', latitud: 6.4, longitud: -75.4 });

    render(<InmueblesMap inmuebles={[uno, dos]} onVerDetalle={jest.fn()} />);

    expect(screen.getByTestId('map-container')).toHaveAttribute(
      'data-center',
      JSON.stringify([6.2, -75.2]),
    );
  });

  it("renders each marker's popup with its foto principal, valor mensual and a 'Ver detalle' action", () => {
    const inmueble = makeInmueble({});

    render(<InmueblesMap inmuebles={[inmueble]} onVerDetalle={jest.fn()} />);

    const popup = screen.getByTestId('popup');
    expect(popup).toHaveTextContent(/1[.,]?500[.,]?000/);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', inmueble.fotoPrincipal as string);
    expect(screen.getByRole('button', { name: /ver detalle/i })).toBeInTheDocument();
  });

  it('calls onVerDetalle(id) when the popup action is clicked', () => {
    const inmueble = makeInmueble({ id: 'inmueble-a-ver' });
    const onVerDetalle = jest.fn();

    render(<InmueblesMap inmuebles={[inmueble]} onVerDetalle={onVerDetalle} />);
    fireEvent.click(screen.getByRole('button', { name: /ver detalle/i }));

    expect(onVerDetalle).toHaveBeenCalledWith('inmueble-a-ver');
  });

  it('does not render an <img> in the popup when fotoPrincipal is null', () => {
    const inmueble = makeInmueble({ fotoPrincipal: null });

    render(<InmueblesMap inmuebles={[inmueble]} onVerDetalle={jest.fn()} />);

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
