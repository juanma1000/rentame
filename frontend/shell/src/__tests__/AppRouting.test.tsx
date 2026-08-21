/**
 * Tasks 14.3 and 14.4 — PrivateLayout routing guard tests.
 *
 * 14.3: Navigating to a protected route WITHOUT an active session must render
 *       the redirect fallback (<Navigate to="/" />) and must NOT render the
 *       protected route's content.
 *
 * 14.4: Navigating to a protected route WITH a valid JWT in localStorage must
 *       render the protected content via <Outlet> and must NOT redirect.
 *
 * Strategy: mock react-router's Navigate and Outlet with testable stubs so
 * the tests focus on PrivateLayout's gating logic rather than on the routing
 * internals. This also keeps the tests independent of react-router's ESM
 * bundle structure, which requires special Jest/CJS handling.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { AuthProvider, storeSession } from '@rentame/auth';

import PrivateLayout from '../layouts/PrivateLayout';

// ---------------------------------------------------------------------------
// Mock react-router — only the slice consumed by PrivateLayout.
// Navigate renders a detectable redirect marker; Outlet renders a content stub.
// ---------------------------------------------------------------------------
jest.mock('react-router', () => ({
  Navigate: ({ to }: { to: string }) => (
    <div data-testid="redirect-navigate" data-to={to} />
  ),
  Outlet: () => <div data-testid="private-outlet">Contenido protegido</div>,
}));

// ---------------------------------------------------------------------------
// Helper: build a structurally-valid (but unsigned) JWT for test assertions.
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

// ---------------------------------------------------------------------------

describe('PrivateLayout routing guard (tasks 14.3 / 14.4)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('14.3 — renders <Navigate to="/" /> and hides protected content when there is no active session', () => {
    render(
      <AuthProvider>
        <PrivateLayout />
      </AuthProvider>,
    );

    // Redirect stub must be present and point to the login entry point.
    expect(screen.getByTestId('redirect-navigate')).toBeInTheDocument();
    expect(screen.getByTestId('redirect-navigate')).toHaveAttribute('data-to', '/');

    // The protected Outlet must NOT be rendered.
    expect(screen.queryByTestId('private-outlet')).not.toBeInTheDocument();
  });

  it('14.4 — renders <Outlet /> (protected content) and does not redirect when a valid session is present', () => {
    // Seed localStorage before mounting AuthProvider so it picks up the
    // session from getSession() during its initialState callback.
    const token = makeToken({ sub: 'user-1', rol: 'propietario', exp: 9_999_999_999 });
    storeSession(token);

    render(
      <AuthProvider>
        <PrivateLayout />
      </AuthProvider>,
    );

    // The protected Outlet must be rendered.
    expect(screen.getByTestId('private-outlet')).toBeInTheDocument();

    // The redirect must NOT be rendered.
    expect(screen.queryByTestId('redirect-navigate')).not.toBeInTheDocument();
  });
});
