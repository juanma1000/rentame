import React from 'react';
import { useAuth } from './useAuth';

export interface AuthGuardProps {
  children: React.ReactNode;
  /**
   * Rendered when there is no active session.
   * Defaults to `null` (renders nothing).
   *
   * Pass `fallback={<Navigate to="/login" replace />}` from the `shell` layer
   * to get redirect behaviour — this component has no dependency on react-router.
   */
  fallback?: React.ReactNode;
}

/**
 * Gate component: renders `children` for authenticated users and `fallback`
 * (default `null`) for unauthenticated ones.
 *
 * Intentionally free of react-router so it can be used in any rendering
 * context. The `shell` layer composes redirect behaviour via `fallback`.
 */
export function AuthGuard({ children, fallback = null }: AuthGuardProps): React.ReactNode {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  return <>{children}</>;
}
