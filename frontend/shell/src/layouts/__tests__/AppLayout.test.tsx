/**
 * Task (Red) — contract test for `layouts/AppLayout.tsx`, per
 * `openspec/changes/ui-layout-navegacion/design.md` (decisions 1-3) and
 * `openspec/changes/ui-layout-navegacion/specs/shell-navegacion/spec.md`
 * ("Layout persistente en toda la aplicación" and "Menú de navegación
 * consciente de la sesión").
 *
 * Contract fixed for this task (`AppLayout` does not exist yet):
 *   - Renders a header with a navigation menu, and a footer with the brand
 *     text "Rentame", both always visible regardless of session state.
 *   - Renders `<Outlet/>` (react-router) so nested route content mounts
 *     inside the layout.
 *   - Menu without an active session: "Inicio" → `/`, "Publicar mi
 *     inmueble" → `/publicar`, "Iniciar sesión" → `/login`. Neither "Mis
 *     inmuebles" nor "Cerrar sesión" are rendered.
 *   - Menu with an active session: "Inicio" → `/`, "Mis inmuebles" →
 *     `/mis-inmuebles`, "Cerrar sesión" (button, calls `useAuth().logout()`).
 *     "Iniciar sesión" is not rendered, and no link with href `/publicar`
 *     exists (per design.md decision 3: "Mis inmuebles" replaces "Publicar
 *     mi inmueble" entirely when there is an active session — same
 *     behavior already fixed for `BusquedaPublicaShellPage` in
 *     `fix/shell-header-session-aware`, now centralized in `AppLayout`).
 *   - Clicking "Cerrar sesión" calls `logout()` from `@rentame/auth` and the
 *     menu re-renders reactively to the "no session" options, without
 *     unmounting/remounting the layout (verified via the observable side
 *     effect: the auth token is cleared from `localStorage`, and "Iniciar
 *     sesión" reappears in the very same render tree after the click).
 *
 * Mock strategy: per this project's established convention for exercising
 * `@rentame/auth`-consuming components (see
 * `frontend/shell/src/pages/__tests__/BusquedaPublicaShellPage.test.tsx`,
 * "session-aware header" block), we wrap with a *real* `AuthProvider` and
 * seed/clear `localStorage['rentame_auth_token']` to control
 * `isAuthenticated`, rather than mocking `useAuth()` directly.
 *
 * `AppLayout` does not exist yet in `../AppLayout` — every test below is
 * expected to fail on import (`Cannot find module '../AppLayout'`), the
 * genuine Red failure for this phase. No implementation is written here.
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';

import AppLayout from '../AppLayout';

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

function renderAppLayout(initialEntry = '/') {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<div>Landing content</div>} />
            <Route path="publicar" element={<div>Publicar page</div>} />
            <Route path="login" element={<div>Login page</div>} />
            <Route path="mis-inmuebles" element={<div>Mis inmuebles page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe('AppLayout (contract, Red)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('without an active session', () => {
    it('renders "Inicio", "Publicar mi inmueble" and "Iniciar sesión" links with the right hrefs', () => {
      renderAppLayout();

      const inicioLink = screen.getByRole('link', { name: /inicio/i });
      expect(inicioLink).toHaveAttribute('href', '/');

      const publicarLink = screen.getByRole('link', { name: /publicar mi inmueble/i });
      expect(publicarLink).toHaveAttribute('href', '/publicar');

      const loginLink = screen.getByRole('link', { name: /iniciar sesión/i });
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('does not render "Mis inmuebles" or "Cerrar sesión"', () => {
      renderAppLayout();

      expect(screen.queryByRole('link', { name: /mis inmuebles/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cerrar sesión/i })).not.toBeInTheDocument();
    });
  });

  describe('with an active session', () => {
    beforeEach(() => {
      localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, TEST_TOKEN);
    });

    it('renders "Inicio" and "Mis inmuebles" links with the right hrefs, and a "Cerrar sesión" button', () => {
      renderAppLayout();

      const inicioLink = screen.getByRole('link', { name: /inicio/i });
      expect(inicioLink).toHaveAttribute('href', '/');

      const misInmueblesLink = screen.getByRole('link', { name: /mis inmuebles/i });
      expect(misInmueblesLink).toHaveAttribute('href', '/mis-inmuebles');

      expect(screen.getByRole('button', { name: /cerrar sesión/i })).toBeInTheDocument();
    });

    it('does not render "Iniciar sesión", nor any link pointing to /publicar', () => {
      renderAppLayout();

      expect(screen.queryByRole('link', { name: /iniciar sesión/i })).not.toBeInTheDocument();

      const publicarHrefLink = screen
        .queryAllByRole('link')
        .find((link) => link.getAttribute('href') === '/publicar');
      expect(publicarHrefLink).toBeUndefined();
    });

    it('clicking "Cerrar sesión" clears the session and the menu reactively shows "Iniciar sesión" again', () => {
      renderAppLayout();

      fireEvent.click(screen.getByRole('button', { name: /cerrar sesión/i }));

      expect(localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)).toBeNull();
      expect(screen.getByRole('link', { name: /iniciar sesión/i })).toHaveAttribute('href', '/login');
      expect(screen.queryByRole('link', { name: /mis inmuebles/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cerrar sesión/i })).not.toBeInTheDocument();
    });
  });

  it('renders the matched child route content via <Outlet/>', () => {
    renderAppLayout('/mis-inmuebles');

    expect(screen.getByText(/mis inmuebles page/i)).toBeInTheDocument();
  });

  it('renders a footer with the "Rentame" brand text, with or without an active session', () => {
    renderAppLayout();
    expect(screen.getByText(/rentame/i)).toBeInTheDocument();

    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, TEST_TOKEN);
    renderAppLayout();
    expect(screen.getAllByText(/rentame/i).length).toBeGreaterThan(0);
  });
});
