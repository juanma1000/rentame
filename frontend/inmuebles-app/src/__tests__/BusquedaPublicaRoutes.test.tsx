/**
 * HU-003 (Red) — `BusquedaPublicaRoutes`, the top-level component exposed by
 * `inmuebles-app` via Module Federation for the public listing/detail flow
 * (per `design.md` decision 5: `./BusquedaPublicaRoutes` in
 * `rspack.config.ts`'s `exposes`).
 *
 * Same navigation pattern as `PropertyRoutes.tsx` (see
 * `src/__tests__/PropertyRoutes.test.tsx`): a local state machine, no nested
 * react-router — the shell already owns the URL for the whole app.
 *
 * `BusquedaPublicaRoutes` does not exist yet — every test below is expected
 * to fail on import (`Cannot find module '../BusquedaPublicaRoutes'`), the
 * genuine Red failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Default view: `BusquedaPublicaPage` (the grid of public listings).
 *   - Clicking a card (which internally calls `BusquedaPublicaPage`'s
 *     `onVerDetalle(id)`) switches the view to `InmuebleDetallePublicoPage`
 *     with that `id` passed as a prop.
 *   - `InmuebleDetallePublicoPage`'s `onVolver` prop, when invoked, switches
 *     the view back to `BusquedaPublicaPage`.
 *   - Mounted at the top with a stable `data-testid` (e.g.
 *     `busqueda-publica-routes`), same convention as `PropertyRoutes`'s
 *     `data-testid="inmuebles-routes"`.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import type { InmueblePublico, InmueblePublicoDetalle } from '../services/inmuebles.api';
import BusquedaPublicaRoutes from '../BusquedaPublicaRoutes';

// frontend-flujo-arrendamiento (task 13.1): `InmuebleDetallePublicoPage`
// (rendered by this state machine's detalle view) now reads `useAuth()` to
// gate the "Solicitar arrendamiento" button — every render needs a real
// `AuthProvider` ancestor.
function renderRoutes() {
  return render(
    <AuthProvider>
      <BusquedaPublicaRoutes />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------
// Mock the full public API surface consumed by the pages rendered inside
// BusquedaPublicaRoutes. `virtual: true` keeps the mock resolvable even
// though `listarPublicos`/`obtenerPublico` don't exist yet on
// `services/inmuebles.api.ts` during this Red phase.
// ---------------------------------------------------------------------------

const mockListarPublicos = jest.fn();
const mockObtenerPublico = jest.fn();

jest.mock(
  '../services/inmuebles.api',
  () => ({
    listarPublicos: (...args: unknown[]) => mockListarPublicos(...args),
    obtenerPublico: (...args: unknown[]) => mockObtenerPublico(...args),
  }),
  { virtual: true },
);

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const INMUEBLE_PUBLICO_FIXTURE: InmueblePublico = {
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
};

const INMUEBLE_DETALLE_FIXTURE: InmueblePublicoDetalle = {
  id: 'inmueble-uuid-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 65,
  habitaciones: 2,
  banos: 1,
  valorMensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
  fotos: [{ urlStorage: 'https://storage.local/foto-1.jpg', orden: 0, esPrincipal: true }],
  latitud: 6.244203,
  longitud: -75.581212,
};

// ---------------------------------------------------------------------------

describe('BusquedaPublicaRoutes (Red — HU-003 state-machine navigation)', () => {
  beforeEach(() => {
    mockListarPublicos.mockReset();
    mockObtenerPublico.mockReset();
  });

  it('renders without throwing', () => {
    mockListarPublicos.mockResolvedValueOnce([]);
    expect(() => renderRoutes()).not.toThrow();
  });

  it('mounts the root container with a stable test id', () => {
    mockListarPublicos.mockResolvedValueOnce([]);
    renderRoutes();
    expect(screen.getByTestId('busqueda-publica-routes')).toBeInTheDocument();
  });

  it('shows BusquedaPublicaPage (listado) as the default view', async () => {
    mockListarPublicos.mockResolvedValueOnce([INMUEBLE_PUBLICO_FIXTURE]);
    renderRoutes();

    expect(await screen.findByText(INMUEBLE_PUBLICO_FIXTURE.direccion)).toBeInTheDocument();
  });

  it('navigates to InmuebleDetallePublicoPage with the correct id when a card is clicked', async () => {
    mockListarPublicos.mockResolvedValueOnce([INMUEBLE_PUBLICO_FIXTURE]);
    mockObtenerPublico.mockResolvedValueOnce(INMUEBLE_DETALLE_FIXTURE);

    renderRoutes();

    const direccionNode = await screen.findByText(INMUEBLE_PUBLICO_FIXTURE.direccion);
    const card =
      direccionNode.closest('li, article, div[data-testid]') ?? direccionNode.parentElement!;
    fireEvent.click(card);

    await waitFor(() =>
      expect(mockObtenerPublico).toHaveBeenCalledWith(INMUEBLE_PUBLICO_FIXTURE.id),
    );
    expect(await screen.findByText(INMUEBLE_DETALLE_FIXTURE.descripcion)).toBeInTheDocument();
  });

  it('returns to the listado view when onVolver is triggered from the detail view', async () => {
    mockListarPublicos.mockResolvedValue([INMUEBLE_PUBLICO_FIXTURE]);
    mockObtenerPublico.mockResolvedValueOnce(INMUEBLE_DETALLE_FIXTURE);

    renderRoutes();

    const direccionNode = await screen.findByText(INMUEBLE_PUBLICO_FIXTURE.direccion);
    const card =
      direccionNode.closest('li, article, div[data-testid]') ?? direccionNode.parentElement!;
    fireEvent.click(card);

    await screen.findByText(INMUEBLE_DETALLE_FIXTURE.descripcion);
    fireEvent.click(screen.getByRole('button', { name: /volver/i }));

    await waitFor(() =>
      expect(screen.queryByText(INMUEBLE_DETALLE_FIXTURE.descripcion)).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('busqueda-publica-routes')).toBeInTheDocument();
  });
});
