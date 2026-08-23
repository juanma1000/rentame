/**
 * Contract test for `pages/BusquedaPublicaShellPage.tsx`.
 *
 * Per `openspec/changes/hu-003/design.md`, decision 5, the public
 * listing/detail flow lives in `inmuebles-app`, exposed via Module
 * Federation as `inmueblesApp/BusquedaPublicaRoutes` (a prop-less component
 * with its own internal listado/detalle state machine — no nested
 * react-router routes needed inside the remote). This page's only
 * remaining responsibility is lazy-loading and rendering that remote
 * inside a `Suspense` boundary (same convention as `MisInmueblesPage`'s
 * "Cargando inmuebles..." fallback for `inmueblesApp/PropertyRoutes`).
 *
 * ---------------------------------------------------------------------------
 * UPDATE (`ui-layout-navegacion`, Green phase): this file previously also
 * covered a session-aware header ("Publicar mi inmueble" / "Iniciar
 * sesión" / "Mis inmuebles" / "Cerrar sesión") that `BusquedaPublicaShellPage`
 * used to compose around the remote itself. That header is now centralized
 * in `layouts/AppLayout.tsx`, which wraps every route — including this one
 * — at the `App.tsx` level (see
 * `openspec/changes/ui-layout-navegacion/design.md`, decisions 1-3). Keeping
 * the header here as well would duplicate it, so `BusquedaPublicaShellPage`
 * no longer renders any header — it is now just the `Suspense` boundary
 * around the lazy-loaded remote. All assertions about that header
 * (originally added across two describe blocks: the initial header contract
 * and the later `fix/shell-header-session-aware` session-aware behavior)
 * have been removed from this file — that header's contract now lives in
 * `frontend/shell/src/layouts/__tests__/AppLayout.test.tsx`, which covers
 * both the unauthenticated and authenticated cases plus reactive logout.
 * ---------------------------------------------------------------------------
 *
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
import { render, screen } from '@testing-library/react';
import React from 'react';

jest.mock(
  'inmueblesApp/BusquedaPublicaRoutes',
  () => ({
    __esModule: true,
    default: () => <div data-testid="busqueda-publica-routes-remote">Remote mounted</div>,
  }),
  { virtual: true },
);

import BusquedaPublicaShellPage from '../BusquedaPublicaShellPage';

describe('BusquedaPublicaShellPage (contract)', () => {
  it('lazy-loads and renders the inmueblesApp/BusquedaPublicaRoutes remote', async () => {
    render(<BusquedaPublicaShellPage />);

    expect(
      await screen.findByTestId('busqueda-publica-routes-remote'),
    ).toBeInTheDocument();
  });
});
