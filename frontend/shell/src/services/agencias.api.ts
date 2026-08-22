/**
 * Minimal HTTP client for the `agencias` backend domain, scoped to what the
 * shell's "paso de agencia" (agente registration flow) needs:
 *   - create a new agencia
 *   - search agencias publicly (no auth)
 *   - request to join an existing agencia
 *
 * This intentionally duplicates the minimal subset of
 * `inmuebles-app/src/services/agencias.api.ts` needed here rather than
 * sharing it — the two microfrontends are independently deployable and
 * neither currently exposes a shared package for this domain. If a third
 * consumer appears, extracting a `@rentame/agencias-client` package would be
 * the natural next step.
 *
 * The base URL follows the same `USUARIOS_API_URL` convention as
 * `services/usuarios.api.ts` (all domains are served by the same backend).
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CrearAgenciaPayload {
  razonSocial: string;
  nit: string;
}

export interface Agencia {
  id: string;
  razonSocial: string;
  nit: string;
}

export interface SolicitudUnion {
  id: string;
  estado: string;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawAgenciaApi {
  id: string;
  razon_social: string;
  nit: string;
}

interface RawSolicitudApi {
  id: string;
  estado: string;
}

function mapAgenciaFromApi(raw: RawAgenciaApi): Agencia {
  return { id: raw.id, razonSocial: raw.razon_social, nit: raw.nit };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

export class AgenciasApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'AgenciasApiError';
    this.status = status;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// ---------------------------------------------------------------------------
// API base URL (shared convention with usuarios.api.ts)
// ---------------------------------------------------------------------------

const BASE_URL = (
  (process.env.USUARIOS_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '');

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * POST `/agencias/` — create a new agencia owned by the authenticated agente.
 *
 * @param payload — razón social and NIT in camelCase
 * @param token   — JWT access token for the `Authorization: Bearer` header
 * @throws {AgenciasApiError} when the server returns a non-2xx status
 */
export async function crearAgencia(
  payload: CrearAgenciaPayload,
  token: string,
): Promise<Agencia> {
  const response = await fetch(`${BASE_URL}/agencias/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      razon_social: payload.razonSocial,
      nit: payload.nit,
    }),
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new AgenciasApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return mapAgenciaFromApi((await response.json()) as RawAgenciaApi);
}

/**
 * GET `/agencias/buscar?q=<texto>` — public search, no `Authorization`
 * header required.
 *
 * @param texto — search text (matched against razón social / NIT)
 * @throws {AgenciasApiError} when the server returns a non-2xx status
 */
export async function buscarAgencias(texto: string): Promise<Agencia[]> {
  const response = await fetch(`${BASE_URL}/agencias/buscar?q=${encodeURIComponent(texto)}`, {
    method: 'GET',
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new AgenciasApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return ((await response.json()) as RawAgenciaApi[]).map(mapAgenciaFromApi);
}

/**
 * POST `/agencias/{agenciaId}/solicitudes` — request to join an existing
 * agencia as the authenticated agente.
 *
 * @param agenciaId — UUID of the agencia to join
 * @param token     — JWT access token for the `Authorization: Bearer` header
 * @throws {AgenciasApiError} when the server returns a non-2xx status
 */
export async function solicitarUnirse(
  agenciaId: string,
  token: string,
): Promise<SolicitudUnion> {
  const response = await fetch(`${BASE_URL}/agencias/${agenciaId}/solicitudes`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new AgenciasApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return (await response.json()) as RawSolicitudApi;
}
