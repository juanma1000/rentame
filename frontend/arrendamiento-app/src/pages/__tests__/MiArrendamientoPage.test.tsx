/**
 * Task 12.1 (Red) — `MiArrendamientoPage` (historial de pagos + pagar el
 * pendiente).
 *
 * Covers the "Página 'Mi arrendamiento' separada del wizard" requirement in
 * `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`.
 *
 * `MiArrendamientoPage` does not exist yet — every test below is expected
 * to fail on import, the genuine Red failure for this phase.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ arrendamientoActivoId: string }`. Fetches
 *     `pagos.api.ts`'s `obtenerHistorial(arrendamientoActivoId, token)` on
 *     mount.
 *   - Shows the full historial (pendientes/completados/fallidos), one row
 *     per `Pago`.
 *   - A "Pagar" button is shown only next to a `Pago` in estado
 *     `pendiente` — none when every pago is `completado`/`fallido`.
 *   - Clicking "Pagar" calls `iniciarPago(pagoId, token)` and reflects the
 *     new estado in the historial once it resolves.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import MiArrendamientoPage from '../MiArrendamientoPage';
import type { Pago } from '../../services/pagos.api';

const mockObtenerHistorial = jest.fn();
const mockIniciarPago = jest.fn();

class MockPagosApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'PagosApiError';
    this.status = status;
  }
}

jest.mock(
  '../../services/pagos.api',
  () => ({
    obtenerHistorial: (...args: unknown[]) => mockObtenerHistorial(...args),
    iniciarPago: (...args: unknown[]) => mockIniciarPago(...args),
    get PagosApiError() {
      return MockPagosApiError;
    },
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

function renderPage(arrendamientoActivoId = 'arrendamiento-uuid-1') {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <MiArrendamientoPage arrendamientoActivoId={arrendamientoActivoId} />
    </AuthProvider>,
  );
}

const pagoPendiente: Pago = {
  id: 'pago-uuid-1',
  arrendamientoActivoId: 'arrendamiento-uuid-1',
  estado: 'pendiente',
  monto: 1_500_000,
  fechaLimite: '2026-10-05',
  fechaPago: null,
  referenciaExterna: null,
};

const pagoCompletado: Pago = {
  id: 'pago-uuid-0',
  arrendamientoActivoId: 'arrendamiento-uuid-1',
  estado: 'completado',
  monto: 1_500_000,
  fechaLimite: '2026-09-05',
  fechaPago: '2026-09-04T10:00:00Z',
  referenciaExterna: 'ref-0',
};

describe('MiArrendamientoPage (Red — frontend-flujo-arrendamiento)', () => {
  beforeEach(() => {
    mockObtenerHistorial.mockReset();
    mockIniciarPago.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('fetches and shows the full historial (pendientes, completados)', async () => {
    mockObtenerHistorial.mockResolvedValueOnce([pagoPendiente, pagoCompletado]);

    renderPage();

    expect(mockObtenerHistorial).toHaveBeenCalledWith('arrendamiento-uuid-1', TEST_TOKEN);
    expect(await screen.findAllByText(/1[.,]?500[.,]?000/)).toHaveLength(2);
    expect(screen.getByText(/pendiente/i)).toBeInTheDocument();
    expect(screen.getByText(/completado/i)).toBeInTheDocument();
  });

  it('shows the "Pagar" button only for the pago pendiente', async () => {
    mockObtenerHistorial.mockResolvedValueOnce([pagoPendiente, pagoCompletado]);

    renderPage();

    await screen.findAllByText(/1[.,]?500[.,]?000/);
    expect(screen.getAllByRole('button', { name: /pagar/i })).toHaveLength(1);
  });

  it('does not show any "Pagar" button when every pago is completado/fallido', async () => {
    mockObtenerHistorial.mockResolvedValueOnce([pagoCompletado]);

    renderPage();

    await screen.findAllByText(/1[.,]?500[.,]?000/);
    expect(screen.queryByRole('button', { name: /pagar/i })).not.toBeInTheDocument();
  });

  it('clicking "Pagar" calls iniciarPago and reflects the new estado', async () => {
    mockObtenerHistorial.mockResolvedValueOnce([pagoPendiente]);
    mockIniciarPago.mockResolvedValueOnce({ ...pagoPendiente, estado: 'completado' });

    renderPage();

    await screen.findByRole('button', { name: /pagar/i });
    fireEvent.click(screen.getByRole('button', { name: /pagar/i }));

    await waitFor(() =>
      expect(mockIniciarPago).toHaveBeenCalledWith(pagoPendiente.id, TEST_TOKEN),
    );

    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /pagar/i })).not.toBeInTheDocument(),
    );
    expect(screen.getByText(/completado/i)).toBeInTheDocument();
  });
});
