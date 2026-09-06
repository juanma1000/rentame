/**
 * Task 9.1 (Red) — `ValidarIdentidadPage` (wizard paso 1: verificar
 * identidad).
 *
 * Covers the "Wizard de 4 pasos en orden estricto" requirement's paso 1 in
 * `openspec/changes/frontend-flujo-arrendamiento/specs/arrendamiento-flujo-ui/spec.md`.
 *
 * `ValidarIdentidadPage` does not exist yet — every test below is expected
 * to fail on import, the genuine Red failure for this phase.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation:
 *
 *   - Props: `{ onSiguiente: () => void }`. The page owns its own fetch of
 *     `identidad.api.ts`'s `obtenerEstado(token)` on mount (token from
 *     `@rentame/auth`'s `useAuth()`, same pattern as `PublicarInmueblePage`).
 *   - `estado === 'no_iniciado' | 'rechazado'` -> shows the form: cédula
 *     input + 2 file inputs (frente/dorso) + submit button.
 *   - `estado === 'aprobado'` -> shows a confirmation message + a
 *     "Siguiente" button that calls `onSiguiente`.
 *   - `estado === 'pendiente'` -> shows a "processing" message (defensive:
 *     the current `FakeAdapter` always resolves synchronously, so this
 *     estado is not reachable via `GET /identidad/estado` after a real
 *     submit, but the wizard should still handle it gracefully instead of
 *     crashing).
 *   - Submitting the form calls `validarIdentidad(cedula, frente, dorso,
 *     token)` and reflects the result: `aprobado` -> confirmation +
 *     "Siguiente"; `rechazado` -> error message, form re-enabled to retry.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import ValidarIdentidadPage from '../ValidarIdentidadPage';

// ---------------------------------------------------------------------------
// Mock the API service — component test, never hits the real backend.
// ---------------------------------------------------------------------------
const mockObtenerEstado = jest.fn();
const mockValidarIdentidad = jest.fn();

class MockIdentidadApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'IdentidadApiError';
    this.status = status;
  }
}

jest.mock(
  '../../services/identidad.api',
  () => ({
    obtenerEstado: (...args: unknown[]) => mockObtenerEstado(...args),
    validarIdentidad: (...args: unknown[]) => mockValidarIdentidad(...args),
    get IdentidadApiError() {
      return MockIdentidadApiError;
    },
  }),
  { virtual: true },
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  return `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(payload)}.test-signature`;
}

const TEST_TOKEN = makeToken({ sub: 'inquilino-uuid-1', rol: 'inquilino', exp: 9_999_999_999 });

function renderPage(onSiguiente: () => void = jest.fn()) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <ValidarIdentidadPage onSiguiente={onSiguiente} />
    </AuthProvider>,
  );
}

function makeFile(name: string): File {
  return new File(['fake-image-bytes'], name, { type: 'image/jpeg' });
}

describe('ValidarIdentidadPage (Red — frontend-flujo-arrendamiento)', () => {
  beforeEach(() => {
    mockObtenerEstado.mockReset();
    mockValidarIdentidad.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('shows the form when estado is no_iniciado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado' });

    renderPage();

    expect(await screen.findByLabelText(/c[eé]dula/i)).toBeInTheDocument();
    expect(mockObtenerEstado).toHaveBeenCalledWith(TEST_TOKEN);
  });

  it('shows the form when estado is rechazado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'rechazado' });

    renderPage();

    expect(await screen.findByLabelText(/c[eé]dula/i)).toBeInTheDocument();
  });

  it('shows a confirmation and a "Siguiente" button when estado is aprobado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'aprobado' });
    const onSiguiente = jest.fn();

    renderPage(onSiguiente);

    const siguiente = await screen.findByRole('button', { name: /siguiente/i });
    fireEvent.click(siguiente);

    expect(onSiguiente).toHaveBeenCalledTimes(1);
  });

  it('submits the form and shows the confirmation when the result is aprobado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado' });
    mockValidarIdentidad.mockResolvedValueOnce({
      id: 'validacion-uuid-1',
      estado: 'aprobado',
      referenciaExterna: 'ref-1',
    });

    renderPage();

    await screen.findByLabelText(/c[eé]dula/i);

    fireEvent.change(screen.getByLabelText(/c[eé]dula/i), { target: { value: '123456789' } });
    fireEvent.change(screen.getByLabelText(/frente/i), {
      target: { files: [makeFile('frente.jpg')] },
    });
    fireEvent.change(screen.getByLabelText(/dorso/i), {
      target: { files: [makeFile('dorso.jpg')] },
    });

    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    await waitFor(() =>
      expect(mockValidarIdentidad).toHaveBeenCalledWith(
        '123456789',
        expect.any(File),
        expect.any(File),
        TEST_TOKEN,
      ),
    );

    expect(await screen.findByRole('button', { name: /siguiente/i })).toBeInTheDocument();
  });

  it('shows an error and keeps the form when the result is rechazado', async () => {
    mockObtenerEstado.mockResolvedValueOnce({ estado: 'no_iniciado' });
    mockValidarIdentidad.mockResolvedValueOnce({
      id: 'validacion-uuid-1',
      estado: 'rechazado',
      referenciaExterna: 'ref-1',
    });

    renderPage();

    await screen.findByLabelText(/c[eé]dula/i);

    fireEvent.change(screen.getByLabelText(/c[eé]dula/i), { target: { value: '123456789' } });
    fireEvent.change(screen.getByLabelText(/frente/i), {
      target: { files: [makeFile('frente.jpg')] },
    });
    fireEvent.change(screen.getByLabelText(/dorso/i), {
      target: { files: [makeFile('dorso.jpg')] },
    });
    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/rechaz/i);
    expect(screen.getByLabelText(/c[eé]dula/i)).toBeInTheDocument();
  });
});
