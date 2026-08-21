/**
 * Tasks 18/19 (Red) — `MisInmueblesPage` (panel "Mis inmuebles" con los
 * controles de despublicar/republicar). Covers tasks 18.1-18.2 and
 * 19.1-19.2 of `openspec/changes/hu-001/tasks.md`, mapped to the
 * "Listado de inmuebles propios" and "Despublicación temporal del inmueble"
 * requirements in `openspec/changes/hu-001/specs/inmuebles/spec.md`.
 *
 * `MisInmueblesPage` does not exist yet — every test below is expected to
 * fail on import (`Cannot find module '../MisInmueblesPage'`), the genuine
 * Red failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation (documented here so
 * `frontend-expert` doesn't have to guess):
 *
 *   - `MisInmueblesPage` takes NO required props. Unlike `EditarInmueblePage`
 *     (which receives its `inmueble` as a prop and never fetches data
 *     itself), this page IS the data-fetching entry point for the "Mis
 *     inmuebles" flow: on mount, it calls `services/inmuebles.api.ts`'s
 *     `listarMisInmuebles(token)` (token from `@rentame/auth`'s `useAuth()`,
 *     `session.token`, exercised through a real `AuthProvider` seeded with a
 *     token in `localStorage`, same pattern as
 *     `EditarInmueblePage.test.tsx`/`PublicarInmueblePage.test.tsx`) and
 *     renders the result.
 *
 *   - Each inmueble in the list renders a status badge with human-readable
 *     text, mapping the domain `estado` value (see
 *     `backend/inmuebles/domain/inmueble.py::EstadoInmueble`) to Spanish
 *     labels:
 *       - `"disponible"`     -> "Disponible"
 *       - `"no_disponible"`  -> "No disponible"
 *       - `"oculto"`         -> "Despublicado"
 *     Matched case-insensitively via `getByText`/`within(...).getByText`
 *     with a regex, so the exact surrounding markup (span/badge component)
 *     is left up to `frontend-expert`.
 *
 *   - Empty state (19.2): when `listarMisInmuebles` resolves `[]`, the page
 *     shows a message matching /no ten[eé]s inmuebles publicados/i instead
 *     of any list markup.
 *
 *   - Despublicar (18.1): an inmueble in `disponible` state renders a button
 *     named "Despublicar" (and NOT "Republicar"). Clicking it calls
 *     `cambiarDisponibilidad(inmueble.id, 'oculto', token)` (mocked here —
 *     component test, not integration/E2E against the real backend). Once
 *     the mocked call resolves, the badge for that inmueble updates to
 *     "Despublicado" WITHOUT the page re-fetching the whole list (i.e.
 *     `listarMisInmuebles` is called exactly once — on mount — proving the
 *     update happens via local state from the `cambiarDisponibilidad`
 *     response, not a full-page reload/refetch).
 *
 *   - Republicar (18.2): an inmueble in `oculto` state renders a button
 *     named "Republicar" (and NOT "Despublicar"). Clicking it calls
 *     `cambiarDisponibilidad(inmueble.id, 'disponible', token)`; the badge
 *     updates to "Disponible", again without re-fetching the list.
 *
 *   - An inmueble in `no_disponible` state renders NEITHER "Despublicar" NOR
 *     "Republicar" — per `design.md`, that transition is only automatic
 *     (triggered by the future `arrendamiento` capability), never a manual
 *     propietario action.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import type { Inmueble } from '../../services/inmuebles.api';
import MisInmueblesPage from '../MisInmueblesPage';

// ---------------------------------------------------------------------------
// Mock the API service — this is a component test, never hits the real
// backend. `listarMisInmuebles`/`cambiarDisponibilidad` do not exist yet in
// `services/inmuebles.api.ts` during this Red phase (tasks 18/19 fix their
// contract in `services/__tests__/inmuebles.api.test.ts`); `{ virtual: true }`
// keeps this test resolvable regardless of that module's current export set.
// ---------------------------------------------------------------------------
const mockListarMisInmuebles = jest.fn();
const mockCambiarDisponibilidad = jest.fn();

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
    listarMisInmuebles: (...args: unknown[]) => mockListarMisInmuebles(...args),
    cambiarDisponibilidad: (...args: unknown[]) => mockCambiarDisponibilidad(...args),
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

function makeInmueble(overrides: Partial<Inmueble>): Inmueble {
  return {
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
    ...overrides,
  };
}

const inmuebleDisponible = makeInmueble({ id: 'inmueble-uuid-1', estado: 'disponible' });
const inmuebleOculto = makeInmueble({ id: 'inmueble-uuid-2', estado: 'oculto' });
const inmuebleNoDisponible = makeInmueble({ id: 'inmueble-uuid-3', estado: 'no_disponible' });

function renderPage() {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <MisInmueblesPage />
    </AuthProvider>,
  );
}

/** Returns the container for the card/row of the given inmueble id, scoped
 * by its `direccion` text (the one field guaranteed to be visible per-card,
 * regardless of the exact markup `frontend-expert` chooses). */
function cardFor(inmueble: Inmueble): HTMLElement {
  const direccionNode = screen.getByText(inmueble.direccion);
  // Walk up to a reasonably-scoped ancestor containing this inmueble's
  // badge/buttons — a `listitem` or generic container role is expected here.
  return direccionNode.closest('li, article, div[data-testid]') ?? direccionNode.parentElement!;
}

// ---------------------------------------------------------------------------

describe('MisInmueblesPage (Red — tasks 18.1-18.2, 19.1-19.2)', () => {
  beforeEach(() => {
    localStorage.clear();
    mockListarMisInmuebles.mockReset();
    mockCambiarDisponibilidad.mockReset();
  });

  // 19.1 --------------------------------------------------------------------
  describe('19.1 — renders the list of own inmuebles with a readable status badge', () => {
    it('fetches the list via listarMisInmuebles(token) on mount and renders each inmueble', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([
        inmuebleDisponible,
        inmuebleOculto,
        inmuebleNoDisponible,
      ]);

      renderPage();

      // All three fixtures share the same `direccion` ('Calle 10 # 20-30') — using
      // findAllByText instead of findByText/getByText because RTL's singular
      // queries throw when multiple elements match the same text.  The assertion
      // below verifies that exactly 3 cards were rendered (one per inmueble).
      const renderedAddresses = await screen.findAllByText(inmuebleDisponible.direccion);
      expect(renderedAddresses).toHaveLength(3);

      expect(mockListarMisInmuebles).toHaveBeenCalledTimes(1);
      expect(mockListarMisInmuebles).toHaveBeenCalledWith(TEST_TOKEN);
    });

    it('maps "disponible" to a "Disponible" badge', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      expect(within(cardFor(inmuebleDisponible)).getByText(/^disponible$/i)).toBeInTheDocument();
    });

    it('maps "no_disponible" to a "No disponible" badge', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleNoDisponible]);

      renderPage();
      await screen.findByText(inmuebleNoDisponible.direccion);

      expect(
        within(cardFor(inmuebleNoDisponible)).getByText(/no disponible/i),
      ).toBeInTheDocument();
    });

    it('maps "oculto" to a "Despublicado" badge', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleOculto]);

      renderPage();
      await screen.findByText(inmuebleOculto.direccion);

      expect(within(cardFor(inmuebleOculto)).getByText(/despublicado/i)).toBeInTheDocument();
    });
  });

  // 19.2 --------------------------------------------------------------------
  describe('19.2 — empty state', () => {
    it('shows an empty-state message when the propietario has no inmuebles published', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([]);

      renderPage();

      expect(
        await screen.findByText(/no ten[eé]s inmuebles publicados/i),
      ).toBeInTheDocument();
    });
  });

  // 18.1 --------------------------------------------------------------------
  describe('18.1 — despublicar a disponible inmueble', () => {
    it('shows a "Despublicar" button for a disponible inmueble', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      expect(
        within(cardFor(inmuebleDisponible)).getByRole('button', { name: /despublicar/i }),
      ).toBeInTheDocument();
      expect(
        within(cardFor(inmuebleDisponible)).queryByRole('button', { name: /republicar/i }),
      ).not.toBeInTheDocument();
    });

    it('calls cambiarDisponibilidad(id, "oculto", token) and updates the badge to "Despublicado" without refetching the whole list', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);
      mockCambiarDisponibilidad.mockResolvedValueOnce({
        ...inmuebleDisponible,
        estado: 'oculto',
      });

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      fireEvent.click(
        within(cardFor(inmuebleDisponible)).getByRole('button', { name: /despublicar/i }),
      );

      await waitFor(() => expect(mockCambiarDisponibilidad).toHaveBeenCalledTimes(1));
      expect(mockCambiarDisponibilidad).toHaveBeenCalledWith(
        inmuebleDisponible.id,
        'oculto',
        TEST_TOKEN,
      );

      expect(
        await within(cardFor(inmuebleDisponible)).findByText(/despublicado/i),
      ).toBeInTheDocument();

      // The update happens from cambiarDisponibilidad's own response, not by
      // re-fetching the full list — no full-page reload of "Mis inmuebles".
      expect(mockListarMisInmuebles).toHaveBeenCalledTimes(1);
    });
  });

  // 18.2 --------------------------------------------------------------------
  describe('18.2 — republicar an oculto inmueble', () => {
    it('shows a "Republicar" button for an oculto inmueble', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleOculto]);

      renderPage();
      await screen.findByText(inmuebleOculto.direccion);

      expect(
        within(cardFor(inmuebleOculto)).getByRole('button', { name: /republicar/i }),
      ).toBeInTheDocument();
      expect(
        within(cardFor(inmuebleOculto)).queryByRole('button', { name: /despublicar/i }),
      ).not.toBeInTheDocument();
    });

    it('calls cambiarDisponibilidad(id, "disponible", token) and updates the badge to "Disponible" without refetching the whole list', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleOculto]);
      mockCambiarDisponibilidad.mockResolvedValueOnce({
        ...inmuebleOculto,
        estado: 'disponible',
      });

      renderPage();
      await screen.findByText(inmuebleOculto.direccion);

      fireEvent.click(
        within(cardFor(inmuebleOculto)).getByRole('button', { name: /republicar/i }),
      );

      await waitFor(() => expect(mockCambiarDisponibilidad).toHaveBeenCalledTimes(1));
      expect(mockCambiarDisponibilidad).toHaveBeenCalledWith(
        inmuebleOculto.id,
        'disponible',
        TEST_TOKEN,
      );

      expect(
        await within(cardFor(inmuebleOculto)).findByText(/^disponible$/i),
      ).toBeInTheDocument();

      expect(mockListarMisInmuebles).toHaveBeenCalledTimes(1);
    });
  });

  // Neither button for the automatic-only "no_disponible" state ------------
  describe('no_disponible inmuebles never show manual publish-state controls', () => {
    it('renders neither "Despublicar" nor "Republicar" for a no_disponible inmueble', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleNoDisponible]);

      renderPage();
      await screen.findByText(inmuebleNoDisponible.direccion);

      const card = cardFor(inmuebleNoDisponible);
      expect(within(card).queryByRole('button', { name: /despublicar/i })).not.toBeInTheDocument();
      expect(within(card).queryByRole('button', { name: /republicar/i })).not.toBeInTheDocument();
    });
  });

  // onEditar and onPublicar optional props (integration with PropertyRoutes) -

  describe('onEditar prop (optional — enables per-card "Editar" button)', () => {
    it('does NOT render an "Editar" button when onEditar is not provided', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage(); // no onEditar
      await screen.findByText(inmuebleDisponible.direccion);

      expect(screen.queryByRole('button', { name: /^editar$/i })).not.toBeInTheDocument();
    });

    it('renders an "Editar" button for each card when onEditar is provided', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible, inmuebleOculto]);

      const onEditar = jest.fn();
      localStorage.setItem('rentame_auth_token', TEST_TOKEN);
      render(
        <AuthProvider>
          <MisInmueblesPage onEditar={onEditar} />
        </AuthProvider>,
      );

      // Both fixtures share the same direccion — use findAllByText to handle
      // the multiple-match case without throwing.
      await screen.findAllByText(inmuebleDisponible.direccion);

      const editarButtons = screen.getAllByRole('button', { name: /^editar$/i });
      expect(editarButtons).toHaveLength(2);
    });

    it('calls onEditar with the correct inmueble when the button is clicked', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      const onEditar = jest.fn();
      localStorage.setItem('rentame_auth_token', TEST_TOKEN);
      render(
        <AuthProvider>
          <MisInmueblesPage onEditar={onEditar} />
        </AuthProvider>,
      );

      await screen.findByText(inmuebleDisponible.direccion);
      fireEvent.click(
        within(cardFor(inmuebleDisponible)).getByRole('button', { name: /^editar$/i }),
      );

      expect(onEditar).toHaveBeenCalledTimes(1);
      expect(onEditar).toHaveBeenCalledWith(inmuebleDisponible);
    });
  });

  describe('onPublicar prop (optional — enables "Publicar nuevo inmueble" button)', () => {
    it('does NOT render a "Publicar nuevo inmueble" button when onPublicar is not provided', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage(); // no onPublicar
      await screen.findByText(inmuebleDisponible.direccion);

      expect(
        screen.queryByRole('button', { name: /publicar nuevo inmueble/i }),
      ).not.toBeInTheDocument();
    });

    it('renders a "Publicar nuevo inmueble" button and calls onPublicar when clicked', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([inmuebleDisponible]);

      const onPublicar = jest.fn();
      localStorage.setItem('rentame_auth_token', TEST_TOKEN);
      render(
        <AuthProvider>
          <MisInmueblesPage onPublicar={onPublicar} />
        </AuthProvider>,
      );

      await screen.findByText(inmuebleDisponible.direccion);
      fireEvent.click(screen.getByRole('button', { name: /publicar nuevo inmueble/i }));

      expect(onPublicar).toHaveBeenCalledTimes(1);
    });

    it('also renders the "Publicar nuevo inmueble" button in the empty state', async () => {
      mockListarMisInmuebles.mockResolvedValueOnce([]);

      const onPublicar = jest.fn();
      localStorage.setItem('rentame_auth_token', TEST_TOKEN);
      render(
        <AuthProvider>
          <MisInmueblesPage onPublicar={onPublicar} />
        </AuthProvider>,
      );

      expect(
        await screen.findByRole('button', { name: /publicar nuevo inmueble/i }),
      ).toBeInTheDocument();
    });
  });
});
