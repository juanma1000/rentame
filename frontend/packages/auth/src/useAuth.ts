import { useContext } from 'react';
import { AuthContext } from './AuthProvider';
import type { AuthContextValue } from './AuthProvider';

/**
 * Consume the authentication context provided by `AuthProvider`.
 *
 * Throws a descriptive error when called outside of an `AuthProvider` so
 * mis-wired components are caught early in development.
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);

  if (ctx === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return ctx;
}
