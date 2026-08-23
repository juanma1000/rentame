/**
 * HU-003 (Red) — `BusquedaPublicaPage` (grid público de inmuebles
 * disponibles, sin autenticación).
 *
 * Covers the "Listado público de inmuebles disponibles" requirement in
 * `openspec/changes/hu-003/specs/inmuebles/spec.md`.
 *
 * `BusquedaPublicaPage` does not exist yet — every test below is expected to
 * fail on import (`Cannot find module '../BusquedaPublicaPage'`), the
 * genuine Red failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - `BusquedaPublicaPage` takes NO required props except `onVerDetalle`
 *     (see below). It is the data-fetching entry point for the public
 *     listing: on mount, it calls `services/inmuebles.api.ts`'s
 *     `listarPublicos()` — NO token, this is an unauthenticated endpoint —
 *     and renders the result as a grid of cards.
 *
 *   - Each card renders, at minimum: the `direccion`/`barrio`, the `ciudad`,
 *     the `valorMensual`, the `habitaciones` count and the `banos` count.
 *     A photo (`<img>`) is rendered when `fotoPrincipal` is not `null`.
 *
 *   - Empty state: when `listarPublicos` resolves `[]`, the page shows a
 *     message matching /no hay inmuebles disponibles/i instead of any grid
 *     markup, and does not crash.
 *
 *   - `onVerDetalle(id: string)` — required prop. Clicking a card invokes it
 *     with that card's inmueble id. Per `design.md` decision 5, this
 *     component does NOT assume react-router (it's exposed via Module
 *     Federation to a host that owns routing) — same pattern as
 *     `PropertyRoutes.tsx`'s pages, which take an `onX` callback prop
 *     instead of navigating directly.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, within } from '@testing-library/react';
import React from 'react';
import type { InmueblePublico } from '../../services/inmuebles.api';
import BusquedaPublicaPage from '../BusquedaPublicaPage';

// ---------------------------------------------------------------------------
// Mock the API service — component test, never hits the real backend.
// `listarPublicos` does not exist yet in `services/inmuebles.api.ts` during
// this Red phase; `{ virtual: true }` keeps this test resolvable regardless
// of that module's current export set.
// ---------------------------------------------------------------------------
const mockListarPublicos = jest.fn();

jest.mock(
  '../../services/inmuebles.api',
  () => ({
    listarPublicos: (...args: unknown[]) => mockListarPublicos(...args),
  }),
  { virtual: true },
);

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeInmueblePublico(overrides: Partial<InmueblePublico>): InmueblePublico {
  return {
    id: 'inmueble-uuid-1',
    fotoPrincipal: 'https://storage.local/foto-1.jpg',
    // Digits chosen to NOT overlap with `habitaciones`/`banos` below —
    // `within(card).getByText(/2/)` would otherwise also match the "20" in
    // this address and fail with "multiple elements found".
    direccion: 'Calle 10 # 20-30',
    barrio: 'Laureles',
    ciudad: 'Medellín',
    valorMensual: 1_500_000,
    habitaciones: 4,
    banos: 6,
    ...overrides,
  };
}

const inmuebleConFoto = makeInmueblePublico({ id: 'inmueble-uuid-1' });
const inmuebleSinFoto = makeInmueblePublico({
  id: 'inmueble-uuid-2',
  fotoPrincipal: null,
  direccion: 'Carrera 50 # 10-20',
  barrio: 'Poblado',
  ciudad: 'Bogotá',
  valorMensual: 2_000_000,
  habitaciones: 3,
  banos: 2,
});

/** Returns the container for the card of the given inmueble, scoped by its
 * `direccion` text (guaranteed visible per-card regardless of markup). */
function cardFor(inmueble: InmueblePublico): HTMLElement {
  const direccionNode = screen.getByText(inmueble.direccion);
  return direccionNode.closest('li, article, div[data-testid]') ?? direccionNode.parentElement!;
}

// ---------------------------------------------------------------------------

describe('BusquedaPublicaPage (Red — HU-003)', () => {
  beforeEach(() => {
    mockListarPublicos.mockReset();
  });

  it('fetches the public listing via listarPublicos() (no token) on mount and renders each inmueble', async () => {
    mockListarPublicos.mockResolvedValueOnce([inmuebleConFoto, inmuebleSinFoto]);

    render(<BusquedaPublicaPage onVerDetalle={jest.fn()} />);

    await screen.findByText(inmuebleConFoto.direccion);
    expect(screen.getByText(inmuebleSinFoto.direccion)).toBeInTheDocument();

    expect(mockListarPublicos).toHaveBeenCalledTimes(1);
    expect(mockListarPublicos).toHaveBeenCalledWith();
  });

  it('renders foto, direccion/barrio, ciudad, valorMensual, habitaciones and banos for a card', async () => {
    mockListarPublicos.mockResolvedValueOnce([inmuebleConFoto]);

    render(<BusquedaPublicaPage onVerDetalle={jest.fn()} />);
    await screen.findByText(inmuebleConFoto.direccion);

    const card = cardFor(inmuebleConFoto);

    expect(within(card).getByText(inmuebleConFoto.barrio, { exact: false })).toBeInTheDocument();
    expect(within(card).getByText(inmuebleConFoto.ciudad, { exact: false })).toBeInTheDocument();
    expect(
      within(card).getByText(/1[.,]?500[.,]?000/),
    ).toBeInTheDocument();
    expect(within(card).getByText(/4/)).toBeInTheDocument(); // habitaciones
    expect(within(card).getByText(/6/)).toBeInTheDocument(); // banos
    expect(within(card).getByRole('img')).toBeInTheDocument();
  });

  it('does not render an <img> for a card whose fotoPrincipal is null', async () => {
    mockListarPublicos.mockResolvedValueOnce([inmuebleSinFoto]);

    render(<BusquedaPublicaPage onVerDetalle={jest.fn()} />);
    await screen.findByText(inmuebleSinFoto.direccion);

    const card = cardFor(inmuebleSinFoto);
    expect(within(card).queryByRole('img')).not.toBeInTheDocument();
  });

  it('shows an empty-state message when there are no inmuebles disponibles, without crashing', async () => {
    mockListarPublicos.mockResolvedValueOnce([]);

    expect(() => render(<BusquedaPublicaPage onVerDetalle={jest.fn()} />)).not.toThrow();

    expect(
      await screen.findByText(/no hay inmuebles disponibles/i),
    ).toBeInTheDocument();
  });

  it('calls onVerDetalle(id) with the correct id when a card is clicked', async () => {
    mockListarPublicos.mockResolvedValueOnce([inmuebleConFoto, inmuebleSinFoto]);
    const onVerDetalle = jest.fn();

    render(<BusquedaPublicaPage onVerDetalle={onVerDetalle} />);
    await screen.findByText(inmuebleConFoto.direccion);

    fireEvent.click(cardFor(inmuebleConFoto));

    expect(onVerDetalle).toHaveBeenCalledTimes(1);
    expect(onVerDetalle).toHaveBeenCalledWith(inmuebleConFoto.id);
  });
});
