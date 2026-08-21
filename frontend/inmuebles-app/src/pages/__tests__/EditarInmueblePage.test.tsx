/**
 * Task 17 (Red) — `EditarInmueblePage` (formulario de edición de un
 * inmueble ya publicado). Covers tasks 17.1-17.2 of
 * `openspec/changes/hu-001/tasks.md`, mapped to the "Edición de inmueble
 * publicado" requirement in `openspec/changes/hu-001/specs/inmuebles/spec.md`
 * (scenario "Propietario edita su propio inmueble").
 *
 * `EditarInmueblePage` does not exist yet — every test below is expected to
 * fail on import (`Cannot find module '../EditarInmueblePage'`), the genuine
 * Red failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Mechanism chosen for "how does the inmueble-to-edit reach the page"
 * (documented here, per the task instructions, so `frontend-expert`
 * implements the same contract instead of guessing):
 *
 *   `EditarInmueblePage` receives the inmueble to edit as a REQUIRED PROP
 *   (`inmueble: Inmueble`), not via route params + an internal fetch. The
 *   page is a pure, fully-controlled form component: it precargues its
 *   local state from `props.inmueble` on mount and never fetches data
 *   itself. This mirrors `PublicarInmueblePage`'s existing "no data-fetching
 *   inside the page" style and keeps this component test a true unit test
 *   (no `obtenerInmueble` service/mock needed here).
 *
 *   The FUTURE route wiring (task 17.3, not part of this Red phase) is
 *   expected to look like:
 *     - `PropertyRoutes.tsx` declares a route (e.g. `/editar/:id`) whose
 *       element resolves the matching `Inmueble` from data already
 *       available in that part of the app (e.g. the list already fetched by
 *       `MisInmueblesPage`/`listarMisInmuebles`, keyed by the route's `:id`
 *       param via `useParams`) and passes it down as the `inmueble` prop.
 *     - No new `obtenerInmueble`/`GET /inmuebles/{id}` service is
 *       introduced by this change: `GET /inmuebles/mios` (already covered
 *       by task 19) is the only read path this feature relies on.
 *
 *   This keeps `EditarInmueblePage` itself decoupled from routing/fetching
 *   concerns, and is the simplest mechanism that satisfies 17.1's
 *   "precarga los datos actuales" requirement without inventing a new
 *   backend contract not present in `router.py`/`schemas.py` (there is no
 *   `GET /inmuebles/{id}` endpoint today).
 * ---------------------------------------------------------------------------
 *
 * Contract this test fixes for the future implementation:
 *   - Props: `{ inmueble: Inmueble }` (see `services/inmuebles.api.ts`'s
 *     `Inmueble` type). No other required props.
 *   - Same field set/labels as `PublicarInmueblePage` (direction, barrio,
 *     ciudad, tipo, area en m², habitaciones, baños, valor mensual,
 *     descripción), each reachable via `getByLabelText`, EXCEPT there is no
 *     fotos input — editing never touches photos (`InmuebleEditRequest` has
 *     no `fotos` field).
 *   - Every field's initial `value` equals the corresponding field on
 *     `props.inmueble` (17.1).
 *   - A submit button named "Guardar cambios".
 *   - On submit, calls `services/inmuebles.api.ts`'s `editarInmueble` with
 *     `(inmueble.id, datos, token)`, where `datos` reflects whatever the
 *     user edited (mocked here — component test, not integration/E2E)
 *     (17.2).
 *   - The `token` passed to the service comes from `@rentame/auth`'s
 *     `useAuth()` (`session.token`), exercised through a real `AuthProvider`
 *     seeded with a token in `localStorage`, exactly like
 *     `PublicarInmueblePage.test.tsx` does.
 *   - On success, shows a confirmation message containing "actualizado".
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import type { Inmueble } from '../../services/inmuebles.api';
import EditarInmueblePage from '../EditarInmueblePage';

// ---------------------------------------------------------------------------
// Mock the API service — this is a component test, never hits the real
// backend. `{ virtual: true }` is required because `services/inmuebles.api.ts`
// does not yet export `editarInmueble` during this Red phase; once task
// 17.3 adds it, the flag remains harmless.
// ---------------------------------------------------------------------------
const mockEditarInmueble = jest.fn();

class MockInmueblesApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'InmueblesApiError';
    this.status = status;
  }
}

// NOTE: same TDZ-avoidance pattern as `PublicarInmueblePage.test.tsx` — the
// getter defers the `MockInmueblesApiError` reference until it's actually
// read at runtime, after the class declaration has been evaluated.
jest.mock(
  '../../services/inmuebles.api',
  () => ({
    editarInmueble: (...args: unknown[]) => mockEditarInmueble(...args),
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

const EXISTING_INMUEBLE: Inmueble = {
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
};

function renderPage(inmueble: Inmueble = EXISTING_INMUEBLE) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <EditarInmueblePage inmueble={inmueble} />
    </AuthProvider>,
  );
}

function submitButton(): HTMLElement {
  return screen.getByRole('button', { name: /guardar cambios/i });
}

// ---------------------------------------------------------------------------

describe('EditarInmueblePage (Red — tasks 17.1-17.2)', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEditarInmueble.mockReset();
  });

  // 17.1 --------------------------------------------------------------------
  describe('17.1 — the form preloads the inmueble current data', () => {
    it('shows every field pre-filled with the values of the inmueble passed as a prop', () => {
      renderPage();

      expect(screen.getByLabelText(/dirección/i)).toHaveValue(EXISTING_INMUEBLE.direccion);
      expect(screen.getByLabelText(/barrio/i)).toHaveValue(EXISTING_INMUEBLE.barrio);
      expect(screen.getByLabelText(/ciudad/i)).toHaveValue(EXISTING_INMUEBLE.ciudad);
      expect(screen.getByLabelText(/tipo de inmueble/i)).toHaveValue(EXISTING_INMUEBLE.tipo);
      expect(screen.getByLabelText(/área.*m/i)).toHaveValue(EXISTING_INMUEBLE.areaM2);
      expect(screen.getByLabelText(/habitaciones/i)).toHaveValue(EXISTING_INMUEBLE.habitaciones);
      expect(screen.getByLabelText(/baños/i)).toHaveValue(EXISTING_INMUEBLE.banos);
      expect(screen.getByLabelText(/valor mensual/i)).toHaveValue(EXISTING_INMUEBLE.valorMensual);
      expect(screen.getByLabelText(/descripción/i)).toHaveValue(EXISTING_INMUEBLE.descripcion);
    });

    it('does not render a fotos input — editing never touches photos', () => {
      renderPage();

      expect(screen.queryByLabelText(/fotos/i)).not.toBeInTheDocument();
    });

    it('starts with the submit button enabled, since every required field is already filled', () => {
      renderPage();

      expect(submitButton()).not.toBeDisabled();
    });
  });

  // 17.2 --------------------------------------------------------------------
  describe('17.2 — successful edit submission', () => {
    it('calls editarInmueble with the inmueble id, the edited data and the JWT, and shows a confirmation message', async () => {
      mockEditarInmueble.mockResolvedValueOnce({
        ...EXISTING_INMUEBLE,
        valorMensual: 1_800_000,
        descripcion: 'Apartamento remodelado, ahora con balcón.',
      });

      renderPage();

      fireEvent.change(screen.getByLabelText(/valor mensual/i), {
        target: { value: '1800000' },
      });
      fireEvent.change(screen.getByLabelText(/descripción/i), {
        target: { value: 'Apartamento remodelado, ahora con balcón.' },
      });

      fireEvent.click(submitButton());

      await waitFor(() => expect(mockEditarInmueble).toHaveBeenCalledTimes(1));

      const [inmuebleId, datos, token] = mockEditarInmueble.mock.calls[0];
      expect(inmuebleId).toBe(EXISTING_INMUEBLE.id);
      expect(datos).toEqual(
        expect.objectContaining({
          direccion: EXISTING_INMUEBLE.direccion,
          barrio: EXISTING_INMUEBLE.barrio,
          ciudad: EXISTING_INMUEBLE.ciudad,
          tipo: EXISTING_INMUEBLE.tipo,
          areaM2: EXISTING_INMUEBLE.areaM2,
          habitaciones: EXISTING_INMUEBLE.habitaciones,
          banos: EXISTING_INMUEBLE.banos,
          valorMensual: 1_800_000,
          descripcion: 'Apartamento remodelado, ahora con balcón.',
        }),
      );
      expect(token).toBe(TEST_TOKEN);

      expect(await screen.findByText(/actualizado/i)).toBeInTheDocument();
    });
  });
});
