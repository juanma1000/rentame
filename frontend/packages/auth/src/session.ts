/**
 * Low-level session storage utilities for @rentame/auth.
 *
 * Stores the raw JWT in localStorage and exposes helpers to read/clear it.
 * Decoding is done client-side with atob() — no signature verification
 * (that happens on the backend for every API request).
 *
 * These utilities are the foundation for AuthProvider/useAuth (tasks 12-14).
 */

import type { AuthSession, JwtPayload } from './auth.types';

const SESSION_KEY = 'rentame_auth_token';

/** Persist a JWT in localStorage. Overwrites any previous value. */
export function storeSession(token: string): void {
  localStorage.setItem(SESSION_KEY, token);
}

/**
 * Retrieve the current session.
 * Returns `null` if there is no stored token or if the stored token is
 * structurally malformed (clears it in that case to avoid stale garbage).
 */
export function getSession(): AuthSession | null {
  const token = localStorage.getItem(SESSION_KEY);
  if (!token) return null;

  const payload = decodeTokenPayload(token);
  if (!payload) {
    // Stale / corrupted token — clean it up.
    clearSession();
    return null;
  }

  return { token, payload };
}

/** Remove the session from localStorage. */
export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

/**
 * Decode the payload section of a JWT without verifying its signature.
 *
 * Returns `null` if:
 *  - The string does not have exactly three dot-separated parts.
 *  - The payload is not valid base64url-encoded JSON.
 *  - The decoded JSON is missing the required `sub` or `rol` string claims.
 */
export function decodeTokenPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    // base64url → standard base64 → add padding → decode
    const base64url = parts[1];
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);

    const decoded: unknown = JSON.parse(atob(padded));

    if (typeof decoded !== 'object' || decoded === null) return null;

    const raw = decoded as Record<string, unknown>;

    if (typeof raw['sub'] !== 'string' || typeof raw['rol'] !== 'string') {
      return null;
    }

    return {
      sub: raw['sub'],
      rol: raw['rol'] as JwtPayload['rol'],
      exp: typeof raw['exp'] === 'number' ? raw['exp'] : undefined,
    };
  } catch {
    return null;
  }
}
