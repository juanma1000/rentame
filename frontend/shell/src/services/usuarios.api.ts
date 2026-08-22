/**
 * HTTP client for the `usuarios` backend domain.
 *
 * Sends JSON requests to the Rentame backend and maps between the camelCase
 * TypeScript interface and the snake_case wire format the backend expects
 * (see `backend/usuarios/infrastructure/api/schemas.py` and `router.py`).
 *
 * Follows the same fetch-based client pattern already established in
 * `inmuebles-app/src/services/inmuebles.api.ts` — no `axios` dependency
 * exists anywhere in this monorepo.
 *
 * The base URL is read from the `USUARIOS_API_URL` environment variable at
 * build time; it falls back to `http://localhost:8000` for local development
 * (same convention as `INMUEBLES_API_URL`).
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Rol = 'propietario' | 'agente' | 'inquilino';

export interface RegistrarPayload {
  email: string;
  password: string;
  nombre: string;
  rol: Rol;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface Usuario {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
}

export interface AuthResult {
  accessToken: string;
  usuario: Usuario;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawUsuarioApi {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
}

interface RawAuthResponseApi {
  access_token: string;
  usuario: RawUsuarioApi;
}

function mapAuthResultFromApi(raw: RawAuthResponseApi): AuthResult {
  return {
    accessToken: raw.access_token,
    usuario: {
      id: raw.usuario.id,
      email: raw.usuario.email,
      nombre: raw.usuario.nombre,
      rol: raw.usuario.rol,
    },
  };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the usuarios API returns a non-2xx response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 409 duplicate email, 422
 *               validation, 401 invalid credentials).
 */
export class UsuariosApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'UsuariosApiError';
    this.status = status;
    // Maintain correct instanceof chain when transpiled to ES5/CJS.
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// ---------------------------------------------------------------------------
// API base URL
// ---------------------------------------------------------------------------

const BASE_URL = (
  (process.env.USUARIOS_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '');

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * POST `/usuarios/registro` — create a new account with a fixed role.
 *
 * @param payload — email, password, nombre and rol in camelCase
 * @returns the created session as `{ accessToken, usuario }`
 * @throws {UsuariosApiError} when the server returns a non-2xx status
 */
export async function registrar(payload: RegistrarPayload): Promise<AuthResult> {
  const response = await fetch(`${BASE_URL}/usuarios/registro`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      nombre: payload.nombre,
      rol: payload.rol,
    }),
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new UsuariosApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return mapAuthResultFromApi((await response.json()) as RawAuthResponseApi);
}

/**
 * POST `/usuarios/login` — authenticate with email and password.
 *
 * @param payload — email and password
 * @returns the created session as `{ accessToken, usuario }`
 * @throws {UsuariosApiError} when the server returns a non-2xx status (401
 *         invalid credentials — a single generic message, indistinguishable
 *         whether the email or the password was wrong)
 */
export async function login(payload: LoginPayload): Promise<AuthResult> {
  const response = await fetch(`${BASE_URL}/usuarios/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
    }),
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new UsuariosApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return mapAuthResultFromApi((await response.json()) as RawAuthResponseApi);
}
