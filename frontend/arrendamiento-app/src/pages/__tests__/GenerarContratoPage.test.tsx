/**
 * Task 11.1 (Red) — `GenerarContratoPage` (wizard paso 3: generar y firmar
 * contrato).
 *
 * Covers the "No se puede acceder al paso de firma sin póliza aprobada" and
 * "El wizard concluye cuando el contrato queda firmado" scenarios in
 * `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`.
 *
 * `GenerarContratoPage` does not exist yet — every test below is expected
 * to fail on import, the genuine Red failure for this phase.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ seguroEstado: EstadoSeguroValue; onVolverASeguro: () =>
 *     void; inmuebleId: string; direccionInmueble: string; canonMensual:
 *     number; onFirmado: (arrendamientoActivoId: string) => void }`.
 *     `inmuebleId`/`direccionInmueble`/`canonMensual` come from the
 *     inmueble the wizard was entered from (see `ArrendamientoRoutes`'s
 *     props) — the backend's `GenerarContratoCommand` needs them and no
 *     domain in this flow can synthesize them (design deviation, see
 *     `services/firma.api.ts`'s docstring).
 *   - `seguroEstado` not `aprobada`/`activa` -> calls `onVolverASeguro()`
 *     on mount, without fetching the firma estado at all.
 *   - Otherwise fetches `firma.api.ts`'s `obtenerEstado(token)`.
 *     `no_iniciado` -> shows the form (nombre inquilino + nombre
 *     propietario + duración en meses, defaulting to 12).
 *     `enviado_a_firma` -> shows a "esperando firma" message.
 *     `firmado` -> calls `onFirmado(arrendamientoActivoId)` immediately.
 *   - Submitting the form calls `generarContrato(datos, token)` with the
 *     full snake_case-mappable input and reflects the result.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import GenerarContratoPage from '../GenerarContratoPage';

const mockObtenerEstado = jest.fn();
const mockGenerarContrato = jest.fn();

class MockFirmaApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'FirmaApiError';
    this.status = status;
  }
}

jest.mock(
  '../../services/firma.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockObtenerEstado(...args),
    generarContrato: (...args: unknown[]) => mockGenerarContrato(...args),
    get FirmaApiError() {
      return MockFirmaApiError;
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

function renderPage(props: Partial<React.ComponentProps<typeof GenerarContratoPage>> = {}) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <GenerarContratoPage
        seguroEstado="aprobada"
        onVolverASeguro={jest.fn()}
        inmuebleId="inmueble-uuid-1"
        direccionInmueble="Calle 10 # 20-30"
        canonMensual={1_500_000}
        onFirmado={jest.fn()}
        {...props}
      />
    </AuthProvider>,
  );
}

describe('GenerarContratoPage (Red — frontend-flujo-arrendamiento)', () => {
  beforeEach(() => {
    mockObtenerEstado.mockReset();
    mockGenerarContrato.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('redirects to paso 2 when seguroEstado is not aprobada/activa, without fetching firma estado', () => {
    const onVolverASeguro = jest.fn();

    renderPage({ seguroEstado: 'no_iniciado', onVolverASeguro });

    expect(onVolverASeguro).toHaveBeenCalledTimes(1);
    expect(mockObtenerEstado).not.toHaveBeenCalled();
  });

  it('shows the form when seguroEstado is aprobada and firma estado is no_iniciado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', arrendamientoActivoId: null });

    renderPage();

    expect(await screen.findByLabelText(/nombre.*inquilino/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/nombre.*propietario/i)).toBeInTheDocument();
  });

  it('shows an "esperando firma" message when firma estado is enviado_a_firma', async () => {
    mockObtenerEstado.mockResolvedValueOnce({
      estado: 'enviado_a_firma',
      arrendamientoActivoId: null,
    });

    renderPage();

    expect(await screen.findByText(/esperando/i)).toBeInTheDocument();
  });

  it('calls onFirmado(arrendamientoActivoId) immediately when firma estado is firmado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({
      estado: 'firmado',
      arrendamientoActivoId: 'arrendamiento-uuid-1',
    });
    const onFirmado = jest.fn();

    renderPage({ onFirmado });

    await waitFor(() => expect(onFirmado).toHaveBeenCalledWith('arrendamiento-uuid-1'));
  });

  it('submits the form and calls onFirmado when the result is enviado_a_firma then firmado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', arrendamientoActivoId: null });
    mockGenerarContrato.mockResolvedValueOnce({
      id: 'contrato-uuid-1',
      estado: 'enviado_a_firma',
      referenciaExterna: 'ref-1',
    });

    renderPage();

    await screen.findByLabelText(/nombre.*inquilino/i);

    fireEvent.change(screen.getByLabelText(/nombre.*inquilino/i), {
      target: { value: 'Juan Pérez' },
    });
    fireEvent.change(screen.getByLabelText(/nombre.*propietario/i), {
      target: { value: 'María Gómez' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generar contrato/i }));

    await waitFor(() =>
      expect(mockGenerarContrato).toHaveBeenCalledWith(
        expect.objectContaining({
          inmuebleId: 'inmueble-uuid-1',
          nombreInquilino: 'Juan Pérez',
          nombrePropietario: 'María Gómez',
          direccionInmueble: 'Calle 10 # 20-30',
          canonMensual: 1_500_000,
          duracionMeses: 12,
        }),
        TEST_TOKEN,
      ),
    );

    expect(await screen.findByText(/esperando/i)).toBeInTheDocument();
  });
});
