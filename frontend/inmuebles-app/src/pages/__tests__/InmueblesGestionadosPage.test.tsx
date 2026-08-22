/**
 * Task 12 (Red) — `InmueblesGestionadosPage` (panel "Inmuebles que gestiono"
 * para el agente autenticado). Covers tasks 12.1-12.2 of
 * `openspec/changes/hu-002/tasks.md`, mapped to the "Listado de inmuebles
 * gestionados por agencia" requirement in
 * `openspec/changes/hu-002/specs/inmuebles/spec.md`.
 *
 * `InmueblesGestionadosPage` does not exist yet — every test below is
 * expected to fail on import
 * (`Cannot find module '../InmueblesGestionadosPage'`), the genuine Red
 * failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Contract this test fixes for the future implementation (documented here so
 * `frontend-expert` doesn't have to guess):
 *
 *   - `InmueblesGestionadosPage` takes no required props. Like
 *     `MisInmueblesPage`, it is the data-fetching entry point for the
 *     "Inmuebles que gestiono" flow: on mount it calls
 *     `services/inmuebles.api.ts`'s `listarInmueblesGestionados(token)`
 *     (token from `@rentame/auth`'s `useAuth()`, `session.token`, exercised
 *     through a real `AuthProvider` seeded with a token in `localStorage`,
 *     same pattern as `MisInmueblesPage.test.tsx`).
 *
 *   - Each inmueble in the list renders a status badge with human-readable
 *     text, using the exact same `estado` -> label mapping as
 *     `MisInmueblesPage` (see `backend/inmuebles/domain/inmueble.py::EstadoInmueble`):
 *       - `"disponible"`     -> "Disponible"
 *       - `"no_disponible"`  -> "No disponible"
 *       - `"oculto"`         -> "Despublicado"
 *     Matched case-insensitively via `getByText`/`within(...).getByText`
 *     with a regex, so the exact surrounding markup is left up to
 *     `frontend-expert`.
 *
 *   - Empty state (12.2): when `listarInmueblesGestionados` resolves `[]`
 *     (the agente's agencia manages no inmuebles), the page shows a message
 *     matching /no gestion[aá]s|no hay inmuebles/i instead of any list
 *     markup.
 *
 *   - This task (12.1-12.2) does NOT require despublicar/republicar/editar
 *     controls on this page — those remain the propietario's own actions
 *     surfaced on `MisInmueblesPage`; the agente-facing panel here is
 *     read-only per the spec scenarios ("consulta el listado"). If a future
 *     task adds management actions here, it will fix that contract in its
 *     own Red phase.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, within } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';
import type { Inmueble } from '../../services/inmuebles.api';
import InmueblesGestionadosPage from '../InmueblesGestionadosPage';

// ---------------------------------------------------------------------------
// Mock the API service — this is a component test, never hits the real
// backend. `listarInmueblesGestionados` does not exist yet in
// `services/inmuebles.api.ts` during this Red phase (its own contract is
// fixed in `services/__tests__/inmuebles.api.test.ts`); `{ virtual: true }`
// keeps this test resolvable regardless of that module's current export set.
// ---------------------------------------------------------------------------
const mockListarInmueblesGestionados = jest.fn();

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
    listarInmueblesGestionados: (...args: unknown[]) => mockListarInmueblesGestionados(...args),
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

const TEST_TOKEN = makeToken({ sub: 'agente-uuid-1', rol: 'agente', exp: 9_999_999_999 });

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

const inmuebleDisponible = makeInmueble({
  id: 'inmueble-uuid-1',
  propietarioId: 'propietario-uuid-1',
  estado: 'disponible',
});
const inmuebleOculto = makeInmueble({
  id: 'inmueble-uuid-2',
  propietarioId: 'propietario-uuid-2',
  estado: 'oculto',
});
const inmuebleNoDisponible = makeInmueble({
  id: 'inmueble-uuid-3',
  propietarioId: 'propietario-uuid-2',
  estado: 'no_disponible',
});

interface PageProps {
  onPublicar?: () => void;
  onEditar?: (inmueble: import('../../services/inmuebles.api').Inmueble) => void;
}

function renderPage() {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <InmueblesGestionadosPage />
    </AuthProvider>,
  );
}

function renderPageWithProps(props: PageProps) {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <InmueblesGestionadosPage {...props} />
    </AuthProvider>,
  );
}

/** Returns the container for the card/row of the given inmueble id, scoped
 * by its `direccion` text (the one field guaranteed to be visible per-card,
 * regardless of the exact markup `frontend-expert` chooses). */
function cardFor(inmueble: Inmueble): HTMLElement {
  const direccionNodes = screen.getAllByText(inmueble.direccion);
  const direccionNode = direccionNodes[0];
  return direccionNode.closest('li, article, div[data-testid]') ?? direccionNode.parentElement!;
}

// ---------------------------------------------------------------------------

describe('InmueblesGestionadosPage (Red — tasks 12.1-12.2)', () => {
  beforeEach(() => {
    localStorage.clear();
    mockListarInmueblesGestionados.mockReset();
  });

  // 12.1 --------------------------------------------------------------------
  describe('12.1 — renders the list of managed inmuebles with a readable status badge', () => {
    it('fetches the list via listarInmueblesGestionados(token) on mount and renders each inmueble', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([
        inmuebleDisponible,
        inmuebleOculto,
        inmuebleNoDisponible,
      ]);

      renderPage();

      // All three fixtures share the same `direccion` ('Calle 10 # 20-30') —
      // using findAllByText instead of findByText/getByText because RTL's
      // singular queries throw when multiple elements match the same text.
      // The assertion below verifies that exactly 3 cards were rendered.
      const renderedAddresses = await screen.findAllByText(inmuebleDisponible.direccion);
      expect(renderedAddresses).toHaveLength(3);

      expect(mockListarInmueblesGestionados).toHaveBeenCalledTimes(1);
      expect(mockListarInmueblesGestionados).toHaveBeenCalledWith(TEST_TOKEN);
    });

    it('maps "disponible" to a "Disponible" badge', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      expect(within(cardFor(inmuebleDisponible)).getByText(/^disponible$/i)).toBeInTheDocument();
    });

    it('maps "no_disponible" to a "No disponible" badge', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleNoDisponible]);

      renderPage();
      await screen.findByText(inmuebleNoDisponible.direccion);

      expect(
        within(cardFor(inmuebleNoDisponible)).getByText(/no disponible/i),
      ).toBeInTheDocument();
    });

    it('maps "oculto" to a "Despublicado" badge', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleOculto]);

      renderPage();
      await screen.findByText(inmuebleOculto.direccion);

      expect(within(cardFor(inmuebleOculto)).getByText(/despublicado/i)).toBeInTheDocument();
    });
  });

  // 12.2 --------------------------------------------------------------------
  describe('12.2 — empty state', () => {
    it('shows an empty-state message when the agente manages no inmuebles', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([]);

      renderPage();

      expect(
        await screen.findByText(/no gestion[aá]s (ning[uú]n )?inmueble|no hay inmuebles/i),
      ).toBeInTheDocument();
    });
  });

  // onEditar prop ----------------------------------------------------------
  describe('onEditar prop', () => {
    it('does not render an Editar button when onEditar is not provided', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      expect(screen.queryByRole('button', { name: /^editar$/i })).not.toBeInTheDocument();
    });

    it('renders an Editar button per card when onEditar is provided', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible, inmuebleOculto]);

      renderPageWithProps({ onEditar: jest.fn() });
      // Both fixtures share the same direccion — use findAllByText
      await screen.findAllByText(inmuebleDisponible.direccion);

      expect(screen.getAllByRole('button', { name: /^editar$/i })).toHaveLength(2);
    });

    it('calls onEditar with the corresponding inmueble when Editar is clicked', async () => {
      const handleEditar = jest.fn();
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPageWithProps({ onEditar: handleEditar });
      await screen.findByText(inmuebleDisponible.direccion);
      fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

      expect(handleEditar).toHaveBeenCalledTimes(1);
      expect(handleEditar).toHaveBeenCalledWith(inmuebleDisponible);
    });
  });

  // onPublicar prop --------------------------------------------------------
  describe('onPublicar prop', () => {
    it('does not render a Publicar button when onPublicar is not provided', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPage();
      await screen.findByText(inmuebleDisponible.direccion);

      expect(
        screen.queryByRole('button', { name: /publicar nuevo inmueble/i }),
      ).not.toBeInTheDocument();
    });

    it('renders a Publicar button when onPublicar is provided (non-empty list)', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPageWithProps({ onPublicar: jest.fn() });
      await screen.findByText(inmuebleDisponible.direccion);

      expect(
        screen.getByRole('button', { name: /publicar nuevo inmueble/i }),
      ).toBeInTheDocument();
    });

    it('renders a Publicar button when onPublicar is provided (empty list)', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([]);

      renderPageWithProps({ onPublicar: jest.fn() });

      expect(
        await screen.findByRole('button', { name: /publicar nuevo inmueble/i }),
      ).toBeInTheDocument();
    });

    it('calls onPublicar when the Publicar button is clicked', async () => {
      const handlePublicar = jest.fn();
      mockListarInmueblesGestionados.mockResolvedValueOnce([inmuebleDisponible]);

      renderPageWithProps({ onPublicar: handlePublicar });
      await screen.findByText(inmuebleDisponible.direccion);
      fireEvent.click(screen.getByRole('button', { name: /publicar nuevo inmueble/i }));

      expect(handlePublicar).toHaveBeenCalledTimes(1);
    });
  });
});
