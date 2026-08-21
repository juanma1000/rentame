import React, { createContext, useState, useCallback } from 'react';
import type { AuthSession, JwtPayload, Role } from './auth.types';
import { getSession, storeSession, clearSession } from './session';

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
    setSession(getSession());
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
