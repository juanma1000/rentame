/**
 * PropertyRoutes — integration-level smoke tests for the state-machine
 * navigation between MisInmueblesPage, PublicarInmueblePage and
 * EditarInmueblePage.
 *
 * This file replaces the task-15.3 placeholder tests now that the real
 * implementation is in place (task-16+ integration).
 *
 * Strategy: mock the full inmuebles API surface so the component tree never
 * hits the real backend.  AuthProvider is rendered with a token seeded in
 * localStorage so that MisInmueblesPage (which calls useAuth()) can obtain a
 * session.  Detailed behaviour of each page (field validation, API call
 * assertions, badge mapping, etc.) is covered by the per-page test files;
 * this suite focuses on the navigation transitions only.
 */
import '@testing-library/jest-dom';
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AuthProvider } from '@rentame/auth';
import PropertyRoutes from '../PropertyRoutes';
import type { Inmueble } from '../services/inmuebles.api';

// ---------------------------------------------------------------------------
// Mock the full API surface consumed by the pages rendered inside
// PropertyRoutes.  `virtual: true` keeps the mock resolvable even when
// individual exports don't yet exist at mock-evaluation time (harmless once
// they do exist).
// ---------------------------------------------------------------------------

const mockListarMisInmuebles = jest.fn();
const mockListarInmueblesGestionados = jest.fn();
const mockPublicarInmueble = jest.fn();
const mockEditarInmueble = jest.fn();
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
  '../services/inmuebles.api',
  () => ({
    listarMisInmuebles: (...args: unknown[]) => mockListarMisInmuebles(...args),
    listarInmueblesGestionados: (...args: unknown[]) => mockListarInmueblesGestionados(...args),
    publicarInmueble: (...args: unknown[]) => mockPublicarInmueble(...args),
    editarInmueble: (...args: unknown[]) => mockEditarInmueble(...args),
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

const TEST_TOKEN = makeToken({ sub: 'propietario-1', rol: 'propietario', exp: 9_999_999_999 });
const AGENTE_TOKEN = makeToken({ sub: 'agente-1', rol: 'agente', exp: 9_999_999_999 });
const INQUILINO_TOKEN = makeToken({ sub: 'inquilino-1', rol: 'inquilino', exp: 9_999_999_999 });

const INMUEBLE_FIXTURE: Inmueble = {
  id: 'inmueble-uuid-1',
  propietarioId: 'propietario-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 65,
  habitaciones: 2,
  banos: 1,
  valorMensual: 1_500_000,
  descripcion: 'Apartamento luminoso.',
  estado: 'disponible',
  fotos: [],
};

function renderRoutes() {
  localStorage.setItem('rentame_auth_token', TEST_TOKEN);
  return render(
    <AuthProvider>
      <PropertyRoutes />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------

describe('PropertyRoutes (task 16 — state-machine navigation)', () => {
  beforeEach(() => {
    localStorage.clear();
    mockListarMisInmuebles.mockReset();
    mockListarInmueblesGestionados.mockReset();
    mockPublicarInmueble.mockReset();
    mockEditarInmueble.mockReset();
    mockCambiarDisponibilidad.mockReset();
  });

  // ── Smoke ────────────────────────────────────────────────────────────────

  it('renders without throwing', () => {
    mockListarMisInmuebles.mockResolvedValueOnce([]);
    expect(() => renderRoutes()).not.toThrow();
  });

  it('mounts the root container with the expected test id', () => {
    mockListarMisInmuebles.mockResolvedValueOnce([]);
    renderRoutes();
    expect(screen.getByTestId('inmuebles-routes')).toBeInTheDocument();
  });

  // ── Default view: lista ──────────────────────────────────────────────────

  it('shows MisInmueblesPage (lista view) as the default', async () => {
    mockListarMisInmuebles.mockResolvedValueOnce([INMUEBLE_FIXTURE]);
    renderRoutes();
    expect(await screen.findByRole('heading', { name: /mis inmuebles/i })).toBeInTheDocument();
  });

  // ── lista → publicar ─────────────────────────────────────────────────────

  it('navigates to PublicarInmueblePage when "Publicar nuevo inmueble" is clicked', async () => {
    mockListarMisInmuebles.mockResolvedValueOnce([]);
    renderRoutes();

    fireEvent.click(await screen.findByRole('button', { name: /publicar nuevo inmueble/i }));

    expect(screen.getByRole('heading', { name: /publicar inmueble/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /mis inmuebles/i })).not.toBeInTheDocument();
  });

  // ── publicar → lista (Volver) ────────────────────────────────────────────

  it('returns to the lista view when "Volver a mis inmuebles" is clicked from PublicarInmueblePage', async () => {
    // mockResolvedValue (not Once) so the re-mount after Volver also resolves
    mockListarMisInmuebles.mockResolvedValue([]);
    renderRoutes();

    fireEvent.click(await screen.findByRole('button', { name: /publicar nuevo inmueble/i }));
    expect(screen.getByRole('heading', { name: /publicar inmueble/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /volver a mis inmuebles/i }));

    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: /publicar inmueble/i })).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('inmuebles-routes')).toBeInTheDocument();
  });

  // ── lista → editar ────────────────────────────────────────────────────────

  it('navigates to EditarInmueblePage when "Editar" is clicked on a card', async () => {
    mockListarMisInmuebles.mockResolvedValueOnce([INMUEBLE_FIXTURE]);
    renderRoutes();

    await screen.findByText(INMUEBLE_FIXTURE.direccion);
    fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

    expect(screen.getByRole('heading', { name: /editar inmueble/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /mis inmuebles/i })).not.toBeInTheDocument();
  });

  // ── editar → lista (Volver) ───────────────────────────────────────────────

  it('returns to the lista view when "Volver a mis inmuebles" is clicked from EditarInmueblePage', async () => {
    mockListarMisInmuebles.mockResolvedValue([INMUEBLE_FIXTURE]);
    renderRoutes();

    await screen.findByText(INMUEBLE_FIXTURE.direccion);
    fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));
    expect(screen.getByRole('heading', { name: /editar inmueble/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /volver a mis inmuebles/i }));

    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: /editar inmueble/i })).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('inmuebles-routes')).toBeInTheDocument();
  });

  // ── EditarInmueblePage receives the correct inmueble ─────────────────────

  it('passes the selected inmueble to EditarInmueblePage', async () => {
    mockListarMisInmuebles.mockResolvedValueOnce([INMUEBLE_FIXTURE]);
    renderRoutes();

    await screen.findByText(INMUEBLE_FIXTURE.direccion);
    fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

    // EditarInmueblePage pre-fills every field from the prop inmueble.
    // Verify at least the direction field matches the fixture.
    expect(screen.getByLabelText(/dirección/i)).toHaveValue(INMUEBLE_FIXTURE.direccion);
  });

  // ── Agente path ───────────────────────────────────────────────────────────

  describe('agente role — mounts InmueblesGestionadosPage as the lista view', () => {
    function renderRoutesAsAgente() {
      localStorage.setItem('rentame_auth_token', AGENTE_TOKEN);
      return render(
        <AuthProvider>
          <PropertyRoutes />
        </AuthProvider>,
      );
    }

    it('shows InmueblesGestionadosPage (lista view) for agente role', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([INMUEBLE_FIXTURE]);
      renderRoutesAsAgente();
      expect(
        await screen.findByRole('heading', { name: /inmuebles que gestiono/i }),
      ).toBeInTheDocument();
    });

    it('does not mount MisInmueblesPage for agente role', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([]);
      renderRoutesAsAgente();
      // Wait for the agente view to settle
      await screen.findByText(/no gestion[aá]s (ning[uú]n )?inmueble|no hay inmuebles/i);
      expect(screen.queryByRole('heading', { name: /mis inmuebles/i })).not.toBeInTheDocument();
    });

    it('navigates to PublicarInmueblePage when "Publicar nuevo inmueble" is clicked (agente)', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([]);
      renderRoutesAsAgente();

      fireEvent.click(await screen.findByRole('button', { name: /publicar nuevo inmueble/i }));

      expect(screen.getByRole('heading', { name: /publicar inmueble/i })).toBeInTheDocument();
    });

    it('navigates to EditarInmueblePage when "Editar" is clicked on a card (agente)', async () => {
      mockListarInmueblesGestionados.mockResolvedValueOnce([INMUEBLE_FIXTURE]);
      renderRoutesAsAgente();

      await screen.findByText(INMUEBLE_FIXTURE.direccion);
      fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

      expect(screen.getByRole('heading', { name: /editar inmueble/i })).toBeInTheDocument();
    });
  });

  // ── Unsupported role (bug repro) ──────────────────────────────────────────
  //
  // `rol="inquilino"` is a valid account role (registrable since HU-008) but
  // has no inmuebles-management view. Before this fix, neither the
  // `propietario` nor `agente` branch matched, so the "lista" view rendered
  // a completely empty `<div data-testid="inmuebles-routes" />` — a blank
  // page with zero console errors and zero failed network requests,
  // reported by the user after "Publicar mi inmueble" (now session-aware,
  // see BusquedaPublicaShellPage) sent an authenticated inquilino straight
  // to /mis-inmuebles.
  describe('inquilino role — no inmuebles-management view exists yet', () => {
    it('shows an explanatory message instead of rendering blank', async () => {
      localStorage.setItem('rentame_auth_token', INQUILINO_TOKEN);
      render(
        <AuthProvider>
          <PropertyRoutes />
        </AuthProvider>,
      );

      expect(
        await screen.findByText(/no (hay|tenés|tienes) inmuebles para gestionar/i),
      ).toBeInTheDocument();
      expect(mockListarMisInmuebles).not.toHaveBeenCalled();
      expect(mockListarInmueblesGestionados).not.toHaveBeenCalled();
    });
  });
});
