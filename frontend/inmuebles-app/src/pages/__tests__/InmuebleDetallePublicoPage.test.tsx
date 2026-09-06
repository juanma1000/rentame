/**
 * HU-003 (Red) — `InmuebleDetallePublicoPage` (detalle público completo de
 * un inmueble disponible, sin autenticación).
 *
 * Covers the "Detalle público de un inmueble disponible" requirement in
 * `openspec/changes/hu-003/specs/inmuebles/spec.md`.
 *
 * `InmuebleDetallePublicoPage` does not exist yet — every test below is
 * expected to fail on import
 * (`Cannot find module '../InmuebleDetallePublicoPage'`), the genuine Red
 * failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ id: string; onVolver: () => void }`. `id` is the inmueble id
 *     to fetch — this page owns the fetch (no route-param + separate fetch
 *     hook), same "receives id/data as prop, fetches inside" pattern the
 *     rest of `inmuebles-app`'s pages already use.
 *
 *   - On mount, calls `services/inmuebles.api.ts`'s `obtenerPublico(id)` —
 *     NO token, unauthenticated endpoint — and renders every field:
 *     all `fotos` (each as an `<img>`), `descripcion`, `direccion`,
 *     `barrio`, `ciudad`, `tipo`, `areaM2`, `habitaciones`, `banos`,
 *     `valorMensual`.
 *
 *   - 404 handling: when `obtenerPublico` rejects with an
 *     `InmueblesApiError` whose `.status === 404`, the page shows a message
 *     matching /ya no est[aá] disponible/i instead of crashing.
 *
 *   - `onVolver()` — required prop. A "Volver" button/callback that returns
 *     to the listing, available both in the normal detail view and in the
 *     404 view.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import type { InmueblePublicoDetalle } from '../../services/inmuebles.api';
import InmuebleDetallePublicoPage from '../InmuebleDetallePublicoPage';

// ---------------------------------------------------------------------------
// frontend-flujo-arrendamiento (task 13.1) mocks the cross-remote
// arrendamientoApp/ArrendamientoRoutes import — a virtual Module Federation
// module that does not exist as a real file for Jest to resolve, same
// convention as declaring a bare specifier remote in `remotes.d.ts`.
// `{ virtual: true }` lets jest.mock intercept it without real resolution.
// ---------------------------------------------------------------------------
const mockArrendamientoRoutesRender = jest.fn();

jest.mock(
  'arrendamientoApp/ArrendamientoRoutes',
  () => ({
    __esModule: true,
    default: (props: Record<string, unknown>) => {
      mockArrendamientoRoutesRender(props);
      return <div data-testid="mock-arrendamiento-routes" />;
    },
  }),
  { virtual: true },
);

// ---------------------------------------------------------------------------
// Mock the API service — component test, never hits the real backend.
// `obtenerPublico`/`InmueblesApiError` do not exist yet in
// `services/inmuebles.api.ts` during this Red phase; `{ virtual: true }`
// keeps this test resolvable regardless of that module's current export set.
// ---------------------------------------------------------------------------
const mockObtenerPublico = jest.fn();

class MockInmueblesApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'InmueblesApiError';
    this.status = status;
  }
}

jest.mock(
  '../../services/inmuebles.api',
  () => ({
    obtenerPublico: (...args: unknown[]) => mockObtenerPublico(...args),
    get InmueblesApiError() {
      return MockInmueblesApiError;
    },
  }),
  { virtual: true },
);

// ---------------------------------------------------------------------------
// Auth helpers (frontend-flujo-arrendamiento, task 13.1) — every test now
// renders inside a real `AuthProvider`, since the page reads `useAuth()` to
// gate the "Solicitar arrendamiento" button by role.
// ---------------------------------------------------------------------------

function makeToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  return `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(payload)}.test-signature`;
}

const INQUILINO_TOKEN = makeToken({ sub: 'inquilino-uuid-1', rol: 'inquilino', exp: 9_999_999_999 });
const PROPIETARIO_TOKEN = makeToken({
  sub: 'propietario-uuid-1',
  rol: 'propietario',
  exp: 9_999_999_999,
});
const AGENTE_TOKEN = makeToken({ sub: 'agente-uuid-1', rol: 'agente', exp: 9_999_999_999 });

function renderPage(
  props: Partial<React.ComponentProps<typeof InmuebleDetallePublicoPage>> = {},
  token?: string,
) {
  if (token) {
    localStorage.setItem('rentame_auth_token', token);
  } else {
    localStorage.removeItem('rentame_auth_token');
  }
  return render(
    <AuthProvider>
      <InmuebleDetallePublicoPage id={detalle.id} onVolver={jest.fn()} {...props} />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const detalle: InmueblePublicoDetalle = {
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
  fotos: [
    { urlStorage: 'https://storage.local/foto-1.jpg', orden: 0, esPrincipal: true },
    { urlStorage: 'https://storage.local/foto-2.jpg', orden: 1, esPrincipal: false },
  ],
};

// ---------------------------------------------------------------------------

describe('InmuebleDetallePublicoPage (Red — HU-003)', () => {
  beforeEach(() => {
    mockObtenerPublico.mockReset();
    mockArrendamientoRoutesRender.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('fetches the detail via obtenerPublico(id) (no token) on mount', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);

    renderPage();

    await screen.findByText(detalle.descripcion);
    expect(mockObtenerPublico).toHaveBeenCalledTimes(1);
    expect(mockObtenerPublico).toHaveBeenCalledWith(detalle.id);
  });

  it('renders all fotos, descripcion, direccion, tipo, area, habitaciones, banos and valorMensual', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);

    renderPage();

    await screen.findByText(detalle.descripcion);

    expect(screen.getByText(detalle.direccion, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(detalle.barrio, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(detalle.ciudad, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(detalle.tipo, { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/65/)).toBeInTheDocument();
    expect(screen.getByText(/1[.,]?500[.,]?000/)).toBeInTheDocument();

    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(detalle.fotos.length);
  });

  it('shows a "no longer available" message, without crashing, when obtenerPublico rejects with a 404 InmueblesApiError', async () => {
    mockObtenerPublico.mockRejectedValueOnce(
      new MockInmueblesApiError('Inmueble no encontrado.', 404),
    );

    expect(() => renderPage({ id: 'inmueble-oculto' })).not.toThrow();

    expect(
      await screen.findByText(/ya no est[aá] disponible/i),
    ).toBeInTheDocument();
  });

  it('calls onVolver() when the "Volver" control is activated from the normal detail view', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);
    const onVolver = jest.fn();

    renderPage({ onVolver });
    await screen.findByText(detalle.descripcion);

    fireEvent.click(screen.getByRole('button', { name: /volver/i }));

    expect(onVolver).toHaveBeenCalledTimes(1);
  });

  it('calls onVolver() when the "Volver" control is activated from the 404 view', async () => {
    mockObtenerPublico.mockRejectedValueOnce(
      new MockInmueblesApiError('Inmueble no encontrado.', 404),
    );
    const onVolver = jest.fn();

    renderPage({ id: 'inmueble-oculto', onVolver });
    await screen.findByText(/ya no est[aá] disponible/i);

    fireEvent.click(screen.getByRole('button', { name: /volver/i }));

    expect(onVolver).toHaveBeenCalledTimes(1);
  });

  // -------------------------------------------------------------------------
  // frontend-flujo-arrendamiento (task 13.1, Red) — "Solicitar arrendamiento"
  // entry point.
  //
  // Covers the "Entrada al flujo de arrendamiento desde el detalle del
  // inmueble" requirement in
  // `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`.
  // -------------------------------------------------------------------------

  it('does not show "Solicitar arrendamiento" for a propietario session', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);

    renderPage({}, PROPIETARIO_TOKEN);
    await screen.findByText(detalle.descripcion);

    expect(
      screen.queryByRole('button', { name: /solicitar arrendamiento/i }),
    ).not.toBeInTheDocument();
  });

  it('does not show "Solicitar arrendamiento" for an agente session', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);

    renderPage({}, AGENTE_TOKEN);
    await screen.findByText(detalle.descripcion);

    expect(
      screen.queryByRole('button', { name: /solicitar arrendamiento/i }),
    ).not.toBeInTheDocument();
  });

  it('shows "Solicitar arrendamiento" without an active session, and redirects to login on click', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);
    const onIrALogin = jest.fn();

    renderPage({ onIrALogin });
    await screen.findByText(detalle.descripcion);

    const boton = screen.getByRole('button', { name: /solicitar arrendamiento/i });
    fireEvent.click(boton);

    expect(onIrALogin).toHaveBeenCalledTimes(1);
    expect(mockArrendamientoRoutesRender).not.toHaveBeenCalled();
  });

  it('navigates to the arrendamiento wizard for an inquilino session', async () => {
    mockObtenerPublico.mockResolvedValueOnce(detalle);

    renderPage({}, INQUILINO_TOKEN);
    await screen.findByText(detalle.descripcion);

    const boton = screen.getByRole('button', { name: /solicitar arrendamiento/i });
    fireEvent.click(boton);

    expect(await screen.findByTestId('mock-arrendamiento-routes')).toBeInTheDocument();
    expect(mockArrendamientoRoutesRender).toHaveBeenCalledWith(
      expect.objectContaining({
        inmuebleId: detalle.id,
        direccionInmueble: detalle.direccion,
        canonMensual: detalle.valorMensual,
      }),
    );
  });
});
