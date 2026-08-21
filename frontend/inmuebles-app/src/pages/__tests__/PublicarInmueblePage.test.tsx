/**
 * Task 16 (Red) — `PublicarInmueblePage` (formulario de publicación de
 * inmueble). Covers tasks 16.1-16.4 of
 * `openspec/changes/hu-001/tasks.md`, each mapped to a Given/When/Then
 * scenario in `openspec/changes/hu-001/specs/inmuebles/spec.md`
 * ("Creación de publicación de inmueble", "Carga de fotos en la
 * publicación").
 *
 * `PublicarInmueblePage` does not exist yet — every test below is expected
 * to fail on import (`Cannot find module '../PublicarInmueblePage'`), the
 * genuine Red failure for this phase. No implementation is written here.
 *
 * Contract this test fixes for the future implementation (documented here
 * so `frontend-expert` doesn't have to guess):
 *   - Text/number fields, each reachable via `getByLabelText` with the
 *     accessible names asserted below (direction, barrio, ciudad, tipo,
 *     area en m², habitaciones, baños, valor mensual, descripción).
 *   - A `<input type="file" multiple>` reachable via
 *     `getByLabelText(/fotos/i)`.
 *   - A submit button named "Publicar".
 *   - `services/inmuebles.api.ts`'s `publicarInmueble` is called with
 *     `(datos, fotos, token)` on successful submission (mocked here — this
 *     is a component test, not an integration/E2E test against the real
 *     backend).
 *   - The `token` passed to the service comes from `@rentame/auth`'s
 *     `useAuth()` (`session.token`), exercised here through a real
 *     `AuthProvider` seeded with a token in `localStorage`, exactly like
 *     `shell/src/__tests__/TokenLoginPage.test.tsx` does.
 *
 * Design choices made explicit for tasks 16.2/16.3 (documented per the
 * task instructions, since the spec doesn't dictate exact UI mechanics):
 *   - 16.2 (0 fotos): the submit BUTTON is expected to be disabled with 0
 *     fotos (per 16.1's contract), so this test dispatches the form's
 *     native `submit` event directly (`fireEvent.submit(form)`) to exercise
 *     the same validation path a stray Enter keypress would trigger,
 *     bypassing the disabled button. This is the simplest way to prove the
 *     validation-on-submit defense actually rejects 0 fotos without calling
 *     the service.
 *   - 16.3 (>10 fotos): selecting 11 files at once (a single
 *     `fireEvent.change` on the file input, mirroring choosing 11 files in
 *     one native file-picker dialog) is rejected immediately: an error
 *     message is shown and the selection is not accepted (fotos count
 *     stays at 0, so the submit button remains disabled and the service is
 *     never called).
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import PublicarInmueblePage from '../PublicarInmueblePage';

// ---------------------------------------------------------------------------
// Mock the API service — this is a component test, never hits the real
// backend. `{ virtual: true }` is required because `services/inmuebles.api.ts`
// does not exist yet during this Red phase; once task 16.5 creates it, the
// flag remains harmless (Jest just skips module-resolution for the mock).
// ---------------------------------------------------------------------------
const mockPublicarInmueble = jest.fn();

class MockInmueblesApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'InmueblesApiError';
    this.status = status;
  }
}

// NOTE: `jest.mock` is hoisted by Jest above all `class` declarations, so
// referencing `MockInmueblesApiError` directly in the factory object literal
// would trigger a TDZ ReferenceError at module-load time (before the class
// declaration is reached).  The getter defers the property access to the
// moment it is first read (at runtime, after module initialisation), at which
// point the class has already been assigned — eliminating the TDZ crash.
jest.mock(
  '../../services/inmuebles.api',
  () => ({
    publicarInmueble: (...args: unknown[]) => mockPublicarInmueble(...args),
    get InmueblesApiError() {
      return MockInmueblesApiError;
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

  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const body = encode(payload);
  return `${header}.${body}.test-signature`;
}

const TEST_TOKEN = makeToken({ sub: 'propietario-uuid-1', rol: 'propietario', exp: 9_999_999_999 });

function renderPage() {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <PublicarInmueblePage />
    </AuthProvider>,
  );
}

function makeFile(name: string): File {
  return new File(['fake-image-bytes'], name, { type: 'image/jpeg' });
}

function makeFiles(count: number): File[] {
  return Array.from({ length: count }, (_, i) => makeFile(`foto-${i + 1}.jpg`));
}

/** Fills every required text/number field with valid data. Leaves fotos untouched. */
function fillRequiredTextFields(): void {
  fireEvent.change(screen.getByLabelText(/dirección/i), {
    target: { value: 'Calle 10 # 20-30' },
  });
  fireEvent.change(screen.getByLabelText(/barrio/i), { target: { value: 'Laureles' } });
  fireEvent.change(screen.getByLabelText(/ciudad/i), { target: { value: 'Medellín' } });
  fireEvent.change(screen.getByLabelText(/tipo de inmueble/i), {
    target: { value: 'apartamento' },
  });
  fireEvent.change(screen.getByLabelText(/área.*m/i), { target: { value: '65' } });
  fireEvent.change(screen.getByLabelText(/habitaciones/i), { target: { value: '2' } });
  fireEvent.change(screen.getByLabelText(/baños/i), { target: { value: '1' } });
  fireEvent.change(screen.getByLabelText(/valor mensual/i), { target: { value: '1500000' } });
  fireEvent.change(screen.getByLabelText(/descripción/i), {
    target: { value: 'Apartamento luminoso cerca al parque.' },
  });
}

function attachFotos(files: File[]): void {
  fireEvent.change(screen.getByLabelText(/fotos/i), { target: { files } });
}

function submitButton(): HTMLElement {
  return screen.getByRole('button', { name: /publicar/i });
}

// ---------------------------------------------------------------------------

describe('PublicarInmueblePage (Red — tasks 16.1-16.4)', () => {
  beforeEach(() => {
    localStorage.clear();
    mockPublicarInmueble.mockReset();
  });

  // 16.1 --------------------------------------------------------------------
  describe('16.1 — the "Publicar" button reflects form completeness', () => {
    it('is disabled when the form is empty', () => {
      renderPage();

      expect(submitButton()).toBeDisabled();
    });

    it('remains disabled once every required field is filled but no photo is attached', () => {
      renderPage();
      fillRequiredTextFields();

      expect(submitButton()).toBeDisabled();
    });

    it('becomes enabled once every required field is filled and at least 1 photo is attached', () => {
      renderPage();
      fillRequiredTextFields();
      attachFotos(makeFiles(1));

      expect(submitButton()).not.toBeDisabled();
    });
  });

  // 16.2 --------------------------------------------------------------------
  describe('16.2 — submitting with 0 fotos', () => {
    it('shows a validation error and does not call the service', () => {
      const { container } = renderPage();
      fillRequiredTextFields();

      const form = container.querySelector('form');
      expect(form).not.toBeNull();
      fireEvent.submit(form as HTMLFormElement);

      expect(screen.getByRole('alert')).toHaveTextContent(/foto/i);
      expect(mockPublicarInmueble).not.toHaveBeenCalled();
    });
  });

  // 16.3 --------------------------------------------------------------------
  describe('16.3 — attaching more than 10 fotos', () => {
    it('rejects selecting 11 photos at once with a validation error and keeps the submit button disabled', () => {
      renderPage();
      fillRequiredTextFields();

      attachFotos(makeFiles(11));

      expect(screen.getByRole('alert')).toHaveTextContent(/10/);
      expect(submitButton()).toBeDisabled();
      expect(mockPublicarInmueble).not.toHaveBeenCalled();
    });
  });

  // 16.4 --------------------------------------------------------------------
  describe('16.4 — successful submission', () => {
    it('calls publicarInmueble with the entered data, the attached fotos and the JWT, and shows a confirmation message', async () => {
      mockPublicarInmueble.mockResolvedValueOnce({
        id: 'inmueble-uuid-1',
        propietarioId: 'propietario-uuid-1',
        direccion: 'Calle 10 # 20-30',
        barrio: 'Laureles',
        ciudad: 'Medellín',
        tipo: 'apartamento',
        areaM2: 65,
        habitaciones: 2,
        banos: 1,
        valorMensual: 1_500_000,
        descripcion: 'Apartamento luminoso cerca al parque.',
        estado: 'disponible',
        fotos: [],
      });

      renderPage();
      fillRequiredTextFields();
      const fotos = makeFiles(2);
      attachFotos(fotos);

      expect(submitButton()).not.toBeDisabled();
      fireEvent.click(submitButton());

      await waitFor(() => expect(mockPublicarInmueble).toHaveBeenCalledTimes(1));

      const [datos, submittedFotos, token] = mockPublicarInmueble.mock.calls[0];
      expect(datos).toEqual(
        expect.objectContaining({
          direccion: 'Calle 10 # 20-30',
          barrio: 'Laureles',
          ciudad: 'Medellín',
          tipo: 'apartamento',
          areaM2: 65,
          habitaciones: 2,
          banos: 1,
          valorMensual: 1_500_000,
          descripcion: 'Apartamento luminoso cerca al parque.',
        }),
      );
      expect(submittedFotos).toHaveLength(2);
      expect(token).toBe(TEST_TOKEN);

      expect(await screen.findByText(/publicado/i)).toBeInTheDocument();
    });
  });
});
