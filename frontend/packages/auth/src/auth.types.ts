/**
 * Domain types for the Rentame authentication singleton.
 *
 * Mirrors the JWT claims emitted by `backend/shared/infrastructure/auth/jwt_handler.py`:
 *   { sub: <user_id>, rol: <role>, exp: <unix_timestamp> }
 *
 * NOTE: AuthProvider, useAuth, and AuthGuard are scaffolded in tasks 12-14 (TDD).
 * Only low-level session utilities live here for now (tasks 11.3-11.4).
 */

export type Role = 'propietario' | 'agente' | 'inquilino';

/** Claims present in every JWT issued by the backend. */
export interface JwtPayload {
  /** Backend user UUID (`sub` claim — maps to `usuario.id`). */
  sub: string;
  /** User role (`rol` claim). */
  rol: Role;
  /** Expiry timestamp in seconds since epoch (`exp` claim). */
  exp?: number;
}

/** An active client session: the raw token plus its decoded payload. */
export interface AuthSession {
  token: string;
  payload: JwtPayload;
}
