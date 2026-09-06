/**
 * Task 12.3 (Red) — `ArrendamientoRoutes`, the top-level state machine
 * exposed by the arrendamiento-app remote via Module Federation.
 *
 * Covers the "Wizard de 4 pasos en orden estricto" requirement in
 * `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`
 * end-to-end at the orchestration level (each individual page's own gating
 * is already covered by its own test file).
 *
 * `ArrendamientoRoutes` only exists as the task 7.1 scaffold placeholder
 * (`<p>Arrendamiento — próximamente.</p>`) — every test below is expected
 * to fail, the genuine Red failure for this phase.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ inmuebleId?: string; direccionInmueble?: string;
 *     canonMensual?: number }` — present when entered from
 *     `InmuebleDetallePublicoPage` (needed for paso 3), absent when
 *     re-entered later (e.g. via a bookmark/nav item) with an already
 *     firmado contrato.
 *   - On mount, fetches identidad/seguro/firma estado (in parallel) and
 *     picks the first unmet step: identidad -> seguro -> firma ->
 *     "Mi arrendamiento" (when firma.estado === 'firmado').
 *   - Each step's own page component receives the callbacks needed to
 *     advance/retreat (already unit-tested individually); this test only
 *     asserts the ROUTING decision made from the 3 fetched estados.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import ArrendamientoRoutes from '../ArrendamientoRoutes';

const mockIdentidadObtenerEstado = jest.fn();
const mockSeguroObtenerEstado = jest.fn();
const mockFirmaObtenerEstado = jest.fn();
const mockPagosObtenerHistorial = jest.fn();

jest.mock(
  '../services/identidad.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockIdentidadObtenerEstado(...args),
    validarIdentidad: jest.fn(),
    IdentidadApiError: class extends Error {},
  }),
  { virtual: true },
);

jest.mock(
  '../services/seguro.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockSeguroObtenerEstado(...args),
    contratarSeguro: jest.fn(),
    SeguroApiError: class extends Error {},
  }),
  { virtual: true },
);

jest.mock(
  '../services/firma.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockFirmaObtenerEstado(...args),
    generarContrato: jest.fn(),
    FirmaApiError: class extends Error {},
  }),
  { virtual: true },
);

jest.mock(
  '../services/pagos.api',
  () => ({
    obtenerHistorial: (...args: unknown[]) => mockPagosObtenerHistorial(...args),
    iniciarPago: jest.fn(),
    PagosApiError: class extends Error {},
  }),
  { virtual: true },
);

function makeToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  return `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(payload)}.test-signature`;
}

const TEST_TOKEN = makeToken({ sub: 'inquilino-uuid-1', rol: 'inquilino', exp: 9_999_999_999 });

function renderRoutes(props: Partial<React.ComponentProps<typeof ArrendamientoRoutes>> = {}) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <ArrendamientoRoutes
        inmuebleId="inmueble-uuid-1"
        direccionInmueble="Calle 10 # 20-30"
        canonMensual={1_500_000}
        {...props}
      />
    </AuthProvider>,
  );
}

describe('ArrendamientoRoutes (Red — frontend-flujo-arrendamiento)', () => {
  beforeEach(() => {
    mockIdentidadObtenerEstado.mockReset();
    mockSeguroObtenerEstado.mockReset();
    mockFirmaObtenerEstado.mockReset();
    mockPagosObtenerHistorial.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('shows paso 1 (identidad) when identidad estado is no_iniciado', async () => {
    // Fetched twice: once by ArrendamientoRoutes to decide routing, once
    // more by ValidarIdentidadPage itself (it owns its own fetch — see its
    // own test file). Same double-fetch pattern applies to every step
    // below whose page component is actually rendered.
    mockIdentidadObtenerEstado.mockResolvedValue({ estado: 'no_iniciado' });
    mockSeguroObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', primaMensual: null });
    mockFirmaObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', arrendamientoActivoId: null });

    renderRoutes();

    expect(await screen.findByLabelText(/c[eé]dula/i)).toBeInTheDocument();
  });

  it('shows paso 2 (seguro) when identidad is aprobado but seguro is no_iniciado', async () => {
    mockIdentidadObtenerEstado.mockResolvedValueOnce({ estado: 'aprobado' });
    mockSeguroObtenerEstado.mockResolvedValue({ estado: 'no_iniciado', primaMensual: null });
    mockFirmaObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', arrendamientoActivoId: null });

    renderRoutes();

    expect(await screen.findByRole('heading', { name: /seguro de arrendamiento/i })).toBeInTheDocument();
  });

  it('shows paso 3 (firma) when identidad and seguro are aprobados', async () => {
    mockIdentidadObtenerEstado.mockResolvedValueOnce({ estado: 'aprobado' });
    mockSeguroObtenerEstado.mockResolvedValueOnce({ estado: 'aprobada', primaMensual: 45000 });
    mockFirmaObtenerEstado.mockResolvedValue({ estado: 'no_iniciado', arrendamientoActivoId: null });

    renderRoutes();

    expect(await screen.findByText(/firma del contrato/i)).toBeInTheDocument();
  });

  it('shows "Mi arrendamiento" directly when firma estado is firmado', async () => {
    mockIdentidadObtenerEstado.mockResolvedValueOnce({ estado: 'aprobado' });
    mockSeguroObtenerEstado.mockResolvedValueOnce({ estado: 'aprobada', primaMensual: 45000 });
    mockFirmaObtenerEstado.mockResolvedValueOnce({
      estado: 'firmado',
      arrendamientoActivoId: 'arrendamiento-uuid-1',
    });
    mockPagosObtenerHistorial.mockResolvedValueOnce([]);

    renderRoutes();

    expect(await screen.findByText(/mi arrendamiento/i)).toBeInTheDocument();
    expect(mockPagosObtenerHistorial).toHaveBeenCalledWith('arrendamiento-uuid-1', TEST_TOKEN);
  });
});
