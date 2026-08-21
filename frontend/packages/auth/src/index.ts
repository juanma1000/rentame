/**
 * @rentame/auth — public API
 *
 * Tasks 11.3-11.4: types + low-level session utilities.
 * Tasks 13.1-13.3: AuthProvider, useAuth, AuthGuard.
 */
export type { Role, JwtPayload, AuthSession } from './auth.types';
export { storeSession, getSession, clearSession, decodeTokenPayload } from './session';
export { AuthProvider, AuthContext } from './AuthProvider';
export type { AuthContextValue } from './AuthProvider';
export { useAuth } from './useAuth';
export { AuthGuard } from './AuthGuard';
export type { AuthGuardProps } from './AuthGuard';
