/**
 * HTTP client for the `seguro-arrendamiento` backend domain, consumed by the
 * arrendamiento wizard's paso 2 (`ContratarSeguroPage`).
 *
 * Same conventions as `identidad.api.ts`: native `fetch`, camelCase<->
 * snake_case mapping, base URL from an env var with a localhost fallback,
 * a typed `*ApiError` on non-2xx responses.
 *
 * Deviation from tasks.md's literal `contratarSeguro(documentos)` signature:
 * `POST /seguro-arrendamiento/contratar` requires a `cedula` form field too
 * (see `ContratarSeguroArrendamientoCommand` in
 * `backend/seguro_arrendamiento/application/contratar_seguro_arrendamiento.py`)
 * — added as the first parameter, same convention `identidad.api.ts`'s
 * `validarIdentidad` already uses.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * The estados the wizard's paso 2 can observe. `'no_iniciado'` is a
 * synthetic API-layer value (design.md decisión 6) for "no
 * PolizaArrendamiento exists yet".
 */
export type EstadoSeguroValue =
  | 'no_iniciado'
  | 'pendiente'
  | 'aprobada'
  | 'rechazada'
  | 'activa'
  | 'vencida';

export interface EstadoSeguro {
  estado: EstadoSeguroValue;
  primaMensual: number | null;
}

export interface PolizaArrendamiento {
  id: string;
  estado: string;
  primaMensual: number | null;
  referenciaExterna: string | null;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawEstadoSeguroApi {
  estado: string;
  prima_mensual: number | null;
}

interface RawPolizaArrendamientoApi {
  id: string;
  estado: string;
  prima_mensual: number | null;
  referencia_externa: string | null;
}

function mapEstadoFromApi(raw: RawEstadoSeguroApi): EstadoSeguro {
  return {
    estado: raw.estado as EstadoSeguroValue,
    primaMensual: raw.prima_mensual ?? null,
  };
}

function mapPolizaFromApi(raw: RawPolizaArrendamientoApi): PolizaArrendamiento {
  return {
    id: String(raw.id),
    estado: raw.estado,
    primaMensual: raw.prima_mensual,
    referenciaExterna: raw.referencia_externa,
  };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the seguro-arrendamiento API returns a non-2xx
 * response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 401, 403, 422).
 */
export class SeguroApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'SeguroApiError';
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
 * GET `/seguro-arrendamiento/estado` — the authenticated inquilino's current
 * seguro de arrendamiento estado (`no_iniciado` when no
 * `PolizaArrendamiento` exists yet).
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @throws {SeguroApiError} when the server returns a non-2xx status
 */
export async function obtenerEstado(token: string): Promise<EstadoSeguro> {
  const response = await fetch(`${BASE_URL}/seguro-arrendamiento/estado`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new SeguroApiError(await readErrorDetail(response), response.status);
  }

  return mapEstadoFromApi((await response.json()) as RawEstadoSeguroApi);
}

/**
 * POST `/seguro-arrendamiento/contratar` — submit the inquilino's cédula
 * plus the support documents (desprendibles de pago, certificado laboral).
 *
 * @param cedula      — the inquilino's cédula number
 * @param documentos  — 1 or more support document files
 * @param token       — JWT access token for the `Authorization: Bearer` header
 * @returns the created `PolizaArrendamiento` parsed from the 200 JSON response
 * @throws {SeguroApiError} when the server returns a non-2xx status
 */
export async function contratarSeguro(
  cedula: string,
  documentos: File[],
  token: string,
): Promise<PolizaArrendamiento> {
  const form = new FormData();
  form.append('cedula', cedula);
  for (const documento of documentos) {
    form.append('documentos', documento);
  }

  const response = await fetch(`${BASE_URL}/seguro-arrendamiento/contratar`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  });

  if (!response.ok) {
    throw new SeguroApiError(await readErrorDetail(response), response.status);
  }

  return mapPolizaFromApi((await response.json()) as RawPolizaArrendamientoApi);
}
