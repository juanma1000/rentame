/**
 * Task (Red) — contract test for `App.tsx`'s route map being reestructured
 * to nest every route under the new shared `AppLayout`, per
 * `openspec/changes/ui-layout-navegacion/design.md`, decision 1
 * ("`AppLayout` vive en `shell`, envuelve el árbol de rutas completo vía
 * `<Outlet/>`") and the Testing Strategy section ("test de routing —
 * confirma que cada ruta sigue montando la página correcta dentro del
 * nuevo `AppLayout`, sin regresión de HU-003/HU-008").
 *
 * This file does NOT modify `src/__tests__/App.routes.test.tsx` (HU-003) —
 * that file already fixes the route-to-page mapping and must keep passing
 * unmodified. This file adds the complementary assertion introduced by this
 * change: that `AppLayout`'s header (identifiable by the always-present
 * "Inicio" link) is mounted alongside each route's page content, for every
 * existing route — public, protected-unauthenticated (redirect), and
 * protected-authenticated.
 *
 * Mock strategy:
 *   - `../pages/BusquedaPublicaShellPage` is shallow-mocked (same as
 *     `App.routes.test.tsx`) so this suite doesn't need the
 *     `inmueblesApp/BusquedaPublicaRoutes` remote mock.
 *   - `inmueblesApp/PropertyRoutes` (the remote lazy-loaded by
 *     `MisInmueblesPage` for the authenticated `/mis-inmuebles` case) is
 *     mocked with `{ virtual: true }`, same convention as
 *     `src/pages/__tests__/BusquedaPublicaShellPage.test.tsx` mocking
 *     `inmueblesApp/BusquedaPublicaRoutes`.
 *
 * `AppLayout` does not exist yet and `App.tsx` does not yet nest its routes
 * under it — every test below is expected to fail on the "Inicio" link
 * being absent (or, for `/mis-inmuebles` with a session, on the remote not
 * mounting because `App.tsx` doesn't render it inside `AppLayout` yet).
 * That is the genuine Red failure for this phase. No implementation is
 * written here.
 */
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';

jest.mock('../pages/BusquedaPublicaShellPage', () => ({
  __esModule: true,
  default: () => <div data-testid="busqueda-publica-shell-page">Busqueda publica shell page</div>,
}));

jest.mock(
  'inmueblesApp/PropertyRoutes',
  () => ({
    __esModule: true,
    default: () => <div data-testid="property-routes-remote">Property routes remote mounted</div>,
  }),
  { virtual: true },
);

import App from '../App';

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

const AUTH_TOKEN_STORAGE_KEY = 'rentame_auth_token';
const TEST_TOKEN = makeTestToken({ sub: 'propietario-uuid-1', rol: 'propietario', exp: 9_999_999_999 });

function renderAppAt(path: string) {
  window.history.pushState({}, '', path);
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>,
  );
}

describe('App route map nested under AppLayout (Red — ui-layout-navegacion)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('mounts AppLayout\'s header alongside BusquedaPublicaShellPage at "/"', () => {
    renderAppAt('/');

    expect(screen.getByRole('link', { name: /inicio/i })).toHaveAttribute('href', '/');
    expect(screen.getByTestId('busqueda-publica-shell-page')).toBeInTheDocument();
  });

  it('mounts AppLayout\'s header alongside LoginPage at "/login"', () => {
    renderAppAt('/login');

    expect(screen.getByRole('link', { name: /inicio/i })).toHaveAttribute('href', '/');
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('mounts AppLayout\'s header alongside EntradaPage at "/publicar"', () => {
    renderAppAt('/publicar');

    expect(screen.getByRole('link', { name: /inicio/i })).toHaveAttribute('href', '/');
    expect(screen.getByText(/¿qué quieres hacer\?/i)).toBeInTheDocument();
  });

  it('mounts AppLayout\'s header alongside RegistroPage at "/registro/propietario"', () => {
    renderAppAt('/registro/propietario');

    expect(screen.getByRole('link', { name: /inicio/i })).toHaveAttribute('href', '/');
    expect(screen.queryByTestId('busqueda-publica-shell-page')).not.toBeInTheDocument();
    expect(screen.queryByText(/ruta no encontrada/i)).not.toBeInTheDocument();
  });

  it('mounts AppLayout\'s header once (no duplication) when "/mis-inmuebles" redirects to "/" without a session', () => {
    renderAppAt('/mis-inmuebles');

    expect(screen.getAllByRole('link', { name: /inicio/i })).toHaveLength(1);
    expect(screen.getByTestId('busqueda-publica-shell-page')).toBeInTheDocument();
  });

  it('mounts AppLayout\'s header alongside the inmuebles-app remote at "/mis-inmuebles" with an active session', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, TEST_TOKEN);
    renderAppAt('/mis-inmuebles');

    expect(screen.getByRole('link', { name: /inicio/i })).toHaveAttribute('href', '/');
    expect(await screen.findByTestId('property-routes-remote')).toBeInTheDocument();
  });
});
