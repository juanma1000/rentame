/**
 * Task (Red) — contract test for the route map reestructuring in `App.tsx`,
 * per `openspec/changes/hu-003/design.md`, decision 6 ("Reestructuración de
 * rutas en `shell`"):
 *
 *   Antes (HU-008)                          Después (HU-003)
 *   /                → EntradaPage           /                → BusquedaPublicaShellPage
 *   /login           → LoginPage             /login           → LoginPage (sin cambios)
 *   /registro/*      → RegistroPage          /publicar        → EntradaPage (reubicada)
 *                                            /registro/*      → RegistroPage (sin cambios)
 *
 * `EntradaPage` is NOT modified internally — only the route that mounts it
 * changes (`/publicar` instead of `/`). `/mis-inmuebles` keeps its existing
 * behavior (protected route behind `PrivateLayout`), unaffected by this
 * change — verified here only for the unauthenticated-redirect case, since
 * the authenticated case is already covered by
 * `src/__tests__/AppRouting.test.tsx` (which in fact tests `PrivateLayout`
 * directly, not `App.tsx`'s route map — this file is the first to assert the
 * concrete route-to-component mapping declared in `App.tsx`).
 *
 * Mock strategy: `BusquedaPublicaShellPage` composes a lazy-loaded Module
 * Federation remote (`inmueblesApp/BusquedaPublicaRoutes`) internally — see
 * `src/pages/__tests__/BusquedaPublicaShellPage.test.tsx` for that contract.
 * Here we mock `../pages/BusquedaPublicaShellPage` itself (shallow) so this
 * test suite only asserts *routing*, not the page's internal composition —
 * avoiding duplicating the remote-mock setup and keeping this suite fast and
 * focused, same isolation principle already used by `AppRouting.test.tsx`
 * mocking `react-router`'s `Navigate`/`Outlet`.
 *
 * `BusquedaPublicaShellPage` does not exist yet — every test that reaches
 * `/` is expected to fail (either on `App.tsx` still mounting `EntradaPage`
 * at `/`, or on the mock target module not existing), the genuine Red
 * failure for this phase. No implementation is written here.
 */
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { AuthProvider } from '@rentame/auth';

jest.mock('../pages/BusquedaPublicaShellPage', () => ({
  __esModule: true,
  default: () => <div data-testid="busqueda-publica-shell-page">Busqueda publica shell page</div>,
}));

import App from '../App';

function renderAppAt(path: string) {
  window.history.pushState({}, '', path);
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>,
  );
}

describe('App route map (Red — HU-003 reestructuración de rutas)', () => {
  afterEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('mounts BusquedaPublicaShellPage at "/" (new public landing)', () => {
    renderAppAt('/');

    expect(screen.getByTestId('busqueda-publica-shell-page')).toBeInTheDocument();
  });

  it('does NOT mount EntradaPage at "/" anymore', () => {
    renderAppAt('/');

    expect(screen.queryByText(/¿qué quieres hacer\?/i)).not.toBeInTheDocument();
  });

  it('mounts EntradaPage (relocated) at "/publicar"', () => {
    renderAppAt('/publicar');

    expect(screen.getByText(/¿qué quieres hacer\?/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /quiero publicar mi inmueble/i })).toBeInTheDocument();
  });

  it('keeps "/login" mounting LoginPage, unaffected by the restructuring', () => {
    renderAppAt('/login');

    // LoginPage renders an email/password form — presence of the email
    // field is enough to confirm LoginPage (not a 404 or another page) is
    // mounted, without depending on LoginPage's full contract here.
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('keeps "/registro/propietario" mounting RegistroPage rol="propietario", unaffected', () => {
    renderAppAt('/registro/propietario');

    expect(screen.queryByTestId('busqueda-publica-shell-page')).not.toBeInTheDocument();
    expect(screen.queryByText(/ruta no encontrada/i)).not.toBeInTheDocument();
  });

  it('keeps "/mis-inmuebles" protected: redirects to "/" when there is no active session', () => {
    renderAppAt('/mis-inmuebles');

    // PrivateLayout redirects unauthenticated visits to "/", which now
    // mounts BusquedaPublicaShellPage (mocked above) instead of EntradaPage.
    expect(screen.getByTestId('busqueda-publica-shell-page')).toBeInTheDocument();
  });
});
