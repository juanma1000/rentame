import React, { createContext, useState, useCallback } from 'react';
import type { AuthSession, JwtPayload, Role } from './auth.types';
import { getSession, storeSession, clearSession, decodeTokenPayload } from './session';

export interface AuthContextValue {
  session: AuthSession | null;
  payload: JwtPayload | null;
  role: Role | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

/**
 * Internal context — consumers must go through `useAuth`, not this directly.
 * Initialized to `null` so `useAuth` can detect the missing-provider case.
 */
export const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * Provides authentication state to the component tree.
 *
 * Initializes from the persisted session in localStorage via `getSession()`.
 * `login(token)` stores a new JWT and refreshes the state.
 * `logout()` clears storage and resets the state.
 */
export function AuthProvider({ children }: AuthProviderProps): React.ReactElement {
  const [session, setSession] = useState<AuthSession | null>(() => getSession());

  const login = useCallback((token: string) => {
    storeSession(token);
    // Build the reactive state directly from the token we were just handed,
    // rather than round-tripping through `getSession()` — that helper
    // deliberately calls `clearSession()` when a *persisted* token fails to
    // decode (protecting the app on next load from stale/corrupted storage),
    // which would otherwise immediately wipe the token this very call just
    // stored. `login()` only ever receives a token from a caller that just
    // obtained it from the backend, so re-validating it against storage
    // here is unnecessary and actively wrong.
    const payload = decodeTokenPayload(token);
    setSession(payload ? { token, payload } : null);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  const payload: JwtPayload | null = session?.payload ?? null;
  const role: Role | null = payload?.rol ?? null;
  const isAuthenticated = session !== null;

  return (
    <AuthContext.Provider value={{ session, payload, role, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
