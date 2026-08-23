/**
 * Task (Red) — contract test for `pages/BusquedaPublicaShellPage.tsx`.
 *
 * Fixes the contract of `BusquedaPublicaShellPage` BEFORE the implementation
 * exists (TDD Red phase, delegated to qa-expert per `openspec/config.yaml`'s
 * `apply` rule), per `openspec/changes/hu-003/design.md`:
 *
 *   - Decision 5: the public listing/detail flow lives in `inmuebles-app`,
 *     exposed via Module Federation as `inmueblesApp/BusquedaPublicaRoutes`
 *     (a prop-less component with its own internal listado/detalle state
 *     machine — no nested react-router routes needed inside the remote).
 *   - Decision 6: `shell` only composes the header (with "Publicar mi
 *     inmueble" → `/publicar` and "Iniciar sesión" → `/login`) around the
 *     lazy-loaded remote component.
 *   - Testing Strategy section: "tests RTL de la nueva página que compone el
 *     header — verifica que ... el header tiene los 2 links/botones
 *     correctos."
 *
 * Contract assumed for this task (mirrors `pages/MisInmueblesPage.tsx`'s
 * lazy-load pattern for the `inmuebles-app` remote):
 *   - Renders a header with:
 *       - "Publicar mi inmueble" → navigates to `/publicar` (an accessible
 *         link, i.e. rendered via react-router's `Link`).
 *       - "Iniciar sesión" → navigates to `/login` (also an accessible link).
 *   - Below the header, lazy-loads and renders
 *     `inmueblesApp/BusquedaPublicaRoutes` inside a `Suspense` boundary with
 *     a fallback (same convention as `MisInmueblesPage`'s "Cargando
 *     inmuebles..." fallback).
 *
 * `BusquedaPublicaShellPage` does not exist yet in
 * `../BusquedaPublicaShellPage` — every test below is expected to fail on
 * import (`Cannot find module '../BusquedaPublicaShellPage'`), the genuine
 * Red failure for this phase. No implementation is written here.
 *
 * ---------------------------------------------------------------------------
 * Mock strategy: `inmueblesApp/BusquedaPublicaRoutes` is a Module Federation
 * remote import, not resolvable by Jest's normal module resolution (no
 * `inmuebles-app` build artifact exists in this test run, and there is no
 * `moduleNameMapper` entry for it in `jest.config.cjs`). `{ virtual: true }`
 * keeps the mock resolvable regardless — same pattern already used for
 * `inmueblesApp`'s own internal remote-boundary mocks, e.g.
 * `frontend/inmuebles-app/src/__tests__/BusquedaPublicaRoutes.test.tsx`
 * mocking `../services/inmuebles.api`.
 * ---------------------------------------------------------------------------
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';

jest.mock(
  'inmueblesApp/BusquedaPublicaRoutes',
  () => ({
    __esModule: true,
    default: () => <div data-testid="busqueda-publica-routes-remote">Remote mounted</div>,
  }),
  { virtual: true },
);

import BusquedaPublicaShellPage from '../BusquedaPublicaShellPage';

function renderBusquedaPublicaShellPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<BusquedaPublicaShellPage />} />
        <Route path="/publicar" element={<div>Publicar page</div>} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('BusquedaPublicaShellPage (contract, Red)', () => {
  it('renders a "Publicar mi inmueble" link in the header, pointing to /publicar', () => {
    renderBusquedaPublicaShellPage();

    const publicarLink = screen.getByRole('link', { name: /publicar mi inmueble/i });
    expect(publicarLink).toBeInTheDocument();
    expect(publicarLink).toHaveAttribute('href', '/publicar');
  });

  it('renders an "Iniciar sesión" link in the header, pointing to /login', () => {
    renderBusquedaPublicaShellPage();

    const loginLink = screen.getByRole('link', { name: /iniciar sesión/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('navigates to /publicar when "Publicar mi inmueble" is clicked', () => {
    renderBusquedaPublicaShellPage();

    fireEvent.click(screen.getByRole('link', { name: /publicar mi inmueble/i }));

    expect(screen.getByText(/publicar page/i)).toBeInTheDocument();
  });

  it('navigates to /login when "Iniciar sesión" is clicked', () => {
    renderBusquedaPublicaShellPage();

    fireEvent.click(screen.getByRole('link', { name: /iniciar sesión/i }));

    expect(screen.getByText(/login page/i)).toBeInTheDocument();
  });

  it('lazy-loads and renders the inmueblesApp/BusquedaPublicaRoutes remote', async () => {
    renderBusquedaPublicaShellPage();

    expect(
      await screen.findByTestId('busqueda-publica-routes-remote'),
    ).toBeInTheDocument();
  });
});

/**
 * ---------------------------------------------------------------------------
 * Session-aware header — Red phase for `fix/shell-header-session-aware`.
 *
 * Bug: the header above always shows "Publicar mi inmueble" → `/publicar`
 * and "Iniciar sesión" → `/login`, regardless of whether the visitor already
 * has an active session (token in localStorage via `@rentame/auth`). This
 * loses the session visually and re-sends an already-authenticated user
 * through the registration flow.
 *
 * Contract fixed for this fix (agreed with the user, not to be reopened):
 *   - No session (unchanged): "Publicar mi inmueble" → `/publicar`,
 *     "Iniciar sesión" → `/login`. No "Cerrar sesión"/"Mis inmuebles".
 *   - Active session: "Publicar mi inmueble" → `/mis-inmuebles` (not
 *     `/publicar`); a new "Mis inmuebles" link → `/mis-inmuebles`; a new
 *     "Cerrar sesión" button that calls `useAuth().logout()`. No
 *     "Iniciar sesión" link.
 *
 * Mock strategy: per this project's established convention for exercising
 * `@rentame/auth`-consuming components (see
 * `frontend/inmuebles-app/src/pages/__tests__/MisInmueblesPage.test.tsx`),
 * we wrap with a *real* `AuthProvider` and seed/clear
 * `localStorage['rentame_auth_token']` to control `isAuthenticated`, rather
 * than mocking `useAuth()` directly. This also lets the "Cerrar sesión"
 * click be verified through a real, observable side effect (the token being
 * cleared from storage) instead of a mock call.
 *
 * `BusquedaPublicaShellPage` is not session-aware yet — every test in this
 * block is expected to fail for the genuine reason that the header still
 * renders the "no session" links regardless of `isAuthenticated`.
 * ---------------------------------------------------------------------------
 */
const AUTH_TOKEN_STORAGE_KEY = 'rentame_auth_token';

function makeTestToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const body = encode(payload);
  return `${header}.${body}.test-signature`;
}

const TEST_TOKEN = makeTestToken({ sub: 'propietario-uuid-1', rol: 'propietario', exp: 9_999_999_999 });

function renderBusquedaPublicaShellPageWithAuth() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<BusquedaPublicaShellPage />} />
          <Route path="/publicar" element={<div>Publicar page</div>} />
          <Route path="/login" element={<div>Login page</div>} />
          <Route path="/mis-inmuebles" element={<div>Mis inmuebles page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe('BusquedaPublicaShellPage — session-aware header (Red, fix/shell-header-session-aware)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('without an active session', () => {
    it('keeps "Publicar mi inmueble" pointing to /publicar, "Iniciar sesión" pointing to /login, and shows neither "Cerrar sesión" nor "Mis inmuebles"', () => {
      renderBusquedaPublicaShellPageWithAuth();

      const publicarLink = screen.getByRole('link', { name: /publicar mi inmueble/i });
      expect(publicarLink).toHaveAttribute('href', '/publicar');

      const loginLink = screen.getByRole('link', { name: /iniciar sesión/i });
      expect(loginLink).toHaveAttribute('href', '/login');

      expect(screen.queryByRole('button', { name: /cerrar sesión/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /mis inmuebles/i })).not.toBeInTheDocument();
    });
  });

  describe('with an active session', () => {
    beforeEach(() => {
      localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, TEST_TOKEN);
    });

    it('points "Publicar mi inmueble" to /mis-inmuebles instead of /publicar', () => {
      renderBusquedaPublicaShellPageWithAuth();

      const publicarLink = screen.getByRole('link', { name: /publicar mi inmueble/i });
      expect(publicarLink).toHaveAttribute('href', '/mis-inmuebles');
    });

    it('renders a "Mis inmuebles" link pointing to /mis-inmuebles', () => {
      renderBusquedaPublicaShellPageWithAuth();

      const misInmueblesLink = screen.getByRole('link', { name: /mis inmuebles/i });
      expect(misInmueblesLink).toHaveAttribute('href', '/mis-inmuebles');
    });

    it('does not render an "Iniciar sesión" link', () => {
      renderBusquedaPublicaShellPageWithAuth();

      expect(screen.queryByRole('link', { name: /iniciar sesión/i })).not.toBeInTheDocument();
    });

    it('renders a "Cerrar sesión" button that clears the active session when clicked', () => {
      renderBusquedaPublicaShellPageWithAuth();

      const logoutButton = screen.getByRole('button', { name: /cerrar sesión/i });
      fireEvent.click(logoutButton);

      expect(localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)).toBeNull();
    });
  });
});
