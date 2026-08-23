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
