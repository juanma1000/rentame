/**
 * HTTP client for the `identidad` backend domain, consumed by the
 * arrendamiento wizard's paso 1 (`ValidarIdentidadPage`).
 *
 * Sends requests to the Rentame backend and maps between the camelCase
 * TypeScript interfaces and the snake_case field names the backend expects
 * (see `backend/identidad/infrastructure/api/{router,schemas}.py`). Same
 * conventions as `inmuebles-app/src/services/inmuebles.api.ts`: native
 * `fetch`, base URL from an env var with a localhost fallback, a typed
 * `*ApiError` on non-2xx responses.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * The four states the wizard's paso 1 can observe. `'no_iniciado'` is a
 * synthetic API-layer value (see design.md decisión 6) for "no
 * ValidacionIdentidad exists yet" — not a member of the backend's
 * `EstadoValidacion` domain enum.
 */
export type EstadoIdentidadValue = 'no_iniciado' | 'pendiente' | 'aprobado' | 'rechazado';

export interface EstadoIdentidad {
  estado: EstadoIdentidadValue;
}

export interface ValidacionIdentidad {
  id: string;
  estado: string;
  referenciaExterna: string | null;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawEstadoIdentidadApi {
  estado: string;
}

interface RawValidacionIdentidadApi {
  id: string;
  estado: string;
  referencia_externa: string | null;
}

function mapValidacionFromApi(raw: RawValidacionIdentidadApi): ValidacionIdentidad {
  return {
    id: String(raw.id),
    estado: raw.estado,
    referenciaExterna: raw.referencia_externa,
  };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the identidad API returns a non-2xx response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 401, 409, 422).
 */
export class IdentidadApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'IdentidadApiError';
    this.status = status;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

const BASE_URL = (
  (process.env.ARRENDAMIENTO_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '');

async function readErrorDetail(response: Response): Promise<string> {
  const body = (await response.json()) as { detail?: string };
  return body.detail ?? 'Error desconocido';
}

/**
 * GET `/identidad/estado` — the authenticated inquilino's current identidad
 * estado (`no_iniciado` when no `ValidacionIdentidad` exists yet).
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @throws {IdentidadApiError} when the server returns a non-2xx status
 */
export async function obtenerEstado(token: string): Promise<EstadoIdentidad> {
  const response = await fetch(`${BASE_URL}/identidad/estado`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new IdentidadApiError(await readErrorDetail(response), response.status);
  }

  return (await response.json()) as EstadoIdentidad;
}

/**
 * POST `/identidad/validar` — submit the inquilino's cédula plus the
 * document's front/back images.
 *
 * @param cedula        — the inquilino's cédula number
 * @param imagenFrente  — front-of-document image file
 * @param imagenDorso   — back-of-document image file
 * @param token         — JWT access token for the `Authorization: Bearer` header
 * @returns the created `ValidacionIdentidad` parsed from the 200 JSON response
 * @throws {IdentidadApiError} when the server returns a non-2xx status
 */
export async function validarIdentidad(
  cedula: string,
  imagenFrente: File,
  imagenDorso: File,
  token: string,
): Promise<ValidacionIdentidad> {
  const form = new FormData();
  form.append('cedula', cedula);
  form.append('imagen_frente', imagenFrente);
  form.append('imagen_dorso', imagenDorso);

  const response = await fetch(`${BASE_URL}/identidad/validar`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  });

  if (!response.ok) {
    throw new IdentidadApiError(await readErrorDetail(response), response.status);
  }

  return mapValidacionFromApi((await response.json()) as RawValidacionIdentidadApi);
}
