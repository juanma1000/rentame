import React from 'react';
import { Link, Outlet, useLocation } from 'react-router';
import { useAuth } from '@rentame/auth';
import { Home, LogOut } from 'lucide-react';

/**
 * Shared application layout, mounted once at the root of the route tree
 * (see `App.tsx`) and wrapping every route via `<Outlet/>`.
 *
 * Centralizes the session-aware navigation header that previously lived
 * duplicated inside `BusquedaPublicaShellPage` (see
 * `openspec/changes/ui-layout-navegacion/design.md`, decisions 1-3):
 *   - No active session: "Inicio" (`/`), "Publicar mi inmueble"
 *     (`/publicar`), "Iniciar sesión" (`/login`).
 *   - Active session: "Inicio" (`/`), "Mis inmuebles" (`/mis-inmuebles`),
 *     "Cerrar sesión" (calls `useAuth().logout()`). "Publicar mi inmueble"
 *     is fully replaced by "Mis inmuebles" — it does not coexist with
 *     `/publicar` while there is a session.
 *
 * Also renders a persistent footer with the "Rentame" brand text.
 *
 * Visual identity (`openspec/changes/design-system-premium-real-estate/design.md`,
 * decision 8 / spec "Navegación con identidad Navy"): the header uses
 * `--color-primary` (Navy) as background, with `--color-surface` (white)
 * text for contrast, and the active nav link (determined from the current
 * route via `useLocation()`) gets a `--color-accent` (gold) bottom border.
 *
 * Note on "Cerrar sesión": `@rentame/ui`'s `Button` has no variant that
 * renders light text over a dark background — every non-`primary` variant
 * uses `--color-primary` (Navy) as its text color, which would be
 * unreadable against this Navy header, and `primary` renders a Navy
 * background/border that would visually merge into the header. So this
 * action uses a simple inline-styled `<button>` built directly from the
 * design tokens (surface-colored text/border, transparent background)
 * instead of forcing an unsuited `Button` variant.
 */
const NAV_LINK_STYLE: React.CSSProperties = {
  color: 'var(--color-surface)',
  textDecoration: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.4rem',
  paddingBottom: '0.25rem',
  borderBottom: '2px solid transparent',
};

const ACTIVE_NAV_LINK_STYLE: React.CSSProperties = {
  ...NAV_LINK_STYLE,
  borderBottom: '2px solid var(--color-accent)',
};

const AppLayout: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string): boolean => location.pathname === path;

  return (
    <div style={{ backgroundColor: 'var(--color-background)', minHeight: '100vh' }}>
      <header
        style={{
          backgroundColor: 'var(--color-primary)',
          color: 'var(--color-surface)',
          fontFamily: 'sans-serif',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: '1.5rem',
        }}
      >
        <Link to="/" style={isActive('/') ? ACTIVE_NAV_LINK_STYLE : NAV_LINK_STYLE}>
          <Home size={16} />
          Inicio
        </Link>
        {isAuthenticated ? (
          <>
            <Link
              to="/mis-inmuebles"
              style={isActive('/mis-inmuebles') ? ACTIVE_NAV_LINK_STYLE : NAV_LINK_STYLE}
            >
              Mis inmuebles
            </Link>
            <button
              type="button"
              onClick={() => logout()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'transparent',
                border: '1px solid var(--color-surface)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-surface)',
                padding: '0.4rem 0.8rem',
                fontFamily: 'sans-serif',
                cursor: 'pointer',
              }}
            >
              <LogOut size={16} />
              Cerrar sesión
            </button>
          </>
        ) : (
          <>
            <Link to="/publicar" style={NAV_LINK_STYLE}>
              Publicar mi inmueble
            </Link>
            <Link to="/login" style={NAV_LINK_STYLE}>
              Iniciar sesión
            </Link>
          </>
        )}
      </header>
      <Outlet />
      <footer
        style={{
          fontFamily: 'sans-serif',
          padding: '1rem 2rem',
          textAlign: 'center',
          color: 'var(--color-text-secondary)',
          backgroundColor: 'var(--color-background)',
        }}
      >
        <p>Rentame</p>
      </footer>
    </div>
  );
};

export default AppLayout;
