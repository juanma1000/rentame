/**
 * Task 10.1 (Red) — `ContratarSeguroPage` (wizard paso 2: contratar seguro).
 *
 * Covers the "No se puede acceder al paso de seguro sin identidad
 * verificada" scenario in
 * `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`.
 *
 * `ContratarSeguroPage` does not exist yet — every test below is expected
 * to fail on import, the genuine Red failure for this phase.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ identidadEstado: EstadoIdentidadValue; onVolverAIdentidad:
 *     () => void; onSiguiente: () => void }`. `identidadEstado` is passed
 *     down by `ArrendamientoRoutes` (which already fetched it to decide
 *     which step to render) — this page does not re-fetch it.
 *   - `identidadEstado !== 'aprobado'` -> calls `onVolverAIdentidad()`
 *     immediately (on mount), without fetching the seguro estado at all.
 *   - `identidadEstado === 'aprobado'` -> fetches `seguro.api.ts`'s
 *     `obtenerEstado(token)`. `no_iniciado`/`rechazada` -> shows the form
 *     (cédula + documentos upload). `aprobada` -> shows the prima mensual +
 *     a "Siguiente" button that calls `onSiguiente`.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import ContratarSeguroPage from '../ContratarSeguroPage';

const mockObtenerEstado = jest.fn();
const mockContratarSeguro = jest.fn();

class MockSeguroApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'SeguroApiError';
    this.status = status;
  }
}

jest.mock(
  '../../services/seguro.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockObtenerEstado(...args),
    contratarSeguro: (...args: unknown[]) => mockContratarSeguro(...args),
    get SeguroApiError() {
      return MockSeguroApiError;
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

function renderPage(props: Partial<React.ComponentProps<typeof ContratarSeguroPage>> = {}) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <ContratarSeguroPage
        identidadEstado="aprobado"
        onVolverAIdentidad={jest.fn()}
        onSiguiente={jest.fn()}
        {...props}
      />
    </AuthProvider>,
  );
}

function makeFile(name: string): File {
  return new File(['fake-doc-bytes'], name, { type: 'application/pdf' });
}

describe('ContratarSeguroPage (Red — frontend-flujo-arrendamiento)', () => {
  beforeEach(() => {
    mockObtenerEstado.mockReset();
    mockContratarSeguro.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('redirects to paso 1 when identidadEstado is not aprobado, without fetching seguro estado', () => {
    const onVolverAIdentidad = jest.fn();

    renderPage({ identidadEstado: 'pendiente', onVolverAIdentidad });

    expect(onVolverAIdentidad).toHaveBeenCalledTimes(1);
    expect(mockObtenerEstado).not.toHaveBeenCalled();
  });

  it('shows the form when identidadEstado is aprobado and seguro estado is no_iniciado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', primaMensual: null });

    renderPage();

    expect(await screen.findByLabelText(/c[eé]dula/i)).toBeInTheDocument();
  });

  it('shows the prima mensual and a "Siguiente" button when seguro estado is aprobada', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'aprobada', primaMensual: 45000 });
    const onSiguiente = jest.fn();

    renderPage({ onSiguiente });

    expect(await screen.findByText(/45[.,]?000/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /siguiente/i }));

    expect(onSiguiente).toHaveBeenCalledTimes(1);
  });

  it('submits the form and shows the prima mensual when the result is aprobada', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado', primaMensual: null });
    mockContratarSeguro.mockResolvedValueOnce({
      id: 'poliza-uuid-1',
      estado: 'aprobada',
      primaMensual: 45000,
      referenciaExterna: 'ref-1',
    });

    renderPage();

    await screen.findByLabelText(/c[eé]dula/i);

    fireEvent.change(screen.getByLabelText(/c[eé]dula/i), { target: { value: '123456789' } });
    fireEvent.change(screen.getByLabelText(/documentos/i), {
      target: { files: [makeFile('doc.pdf')] },
    });
    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    await waitFor(() =>
      expect(mockContratarSeguro).toHaveBeenCalledWith(
        '123456789',
        expect.arrayContaining([expect.any(File)]),
        TEST_TOKEN,
      ),
    );

    expect(await screen.findByText(/45[.,]?000/)).toBeInTheDocument();
  });
});
