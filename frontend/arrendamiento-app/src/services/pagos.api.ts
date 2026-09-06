/**
 * HTTP client for the `pagos` backend domain, consumed by
 * `MiArrendamientoPage` (historial de pagos + iniciar pago).
 *
 * Same conventions as the other `arrendamiento-app` services: native
 * `fetch`, camelCase<->snake_case mapping, base URL from an env var with a
 * localhost fallback, a typed `*ApiError` on non-2xx responses.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type EstadoPagoValue = 'pendiente' | 'completado' | 'fallido';

export interface Pago {
  id: string;
  arrendamientoActivoId: string;
  estado: EstadoPagoValue;
  monto: number;
  fechaLimite: string;
  fechaPago: string | null;
  referenciaExterna: string | null;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawPagoApi {
  id: string;
  arrendamiento_activo_id: string;
  estado: string;
  monto: number;
  fecha_limite: string;
  fecha_pago: string | null;
  referencia_externa: string | null;
}

interface RawHistorialPagosApi {
  pagos: RawPagoApi[];
}

function mapPagoFromApi(raw: RawPagoApi): Pago {
  return {
    id: String(raw.id),
    arrendamientoActivoId: String(raw.arrendamiento_activo_id),
    estado: raw.estado as EstadoPagoValue,
    monto: raw.monto,
    fechaLimite: raw.fecha_limite,
    fechaPago: raw.fecha_pago,
    referenciaExterna: raw.referencia_externa,
  };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the pagos API returns a non-2xx response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 401, 404, 409).
 */
export class PagosApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'PagosApiError';
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
 * GET `/arrendamientos/{arrendamientoActivoId}/pagos` — the full historial
 * de pagos for that arrendamiento, in any estado.
 *
 * @param arrendamientoActivoId — UUID of the arrendamiento activo
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @throws {PagosApiError} when the server returns a non-2xx status
 */
export async function obtenerHistorial(
  arrendamientoActivoId: string,
  token: string,
): Promise<Pago[]> {
  const response = await fetch(`${BASE_URL}/arrendamientos/${arrendamientoActivoId}/pagos`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new PagosApiError(await readErrorDetail(response), response.status);
  }

  const body = (await response.json()) as RawHistorialPagosApi;
  return body.pagos.map(mapPagoFromApi);
}

/**
 * POST `/pagos/{pagoId}/iniciar` — start the cobro of a `Pago` pendiente.
 *
 * @param pagoId — UUID of the pago to start
 * @param token  — JWT access token for the `Authorization: Bearer` header
 * @returns the updated `Pago` parsed from the 200 JSON response
 * @throws {PagosApiError} when the server returns a non-2xx status
 */
export async function iniciarPago(pagoId: string, token: string): Promise<Pago> {
  const response = await fetch(`${BASE_URL}/pagos/${pagoId}/iniciar`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new PagosApiError(await readErrorDetail(response), response.status);
  }

  return mapPagoFromApi((await response.json()) as RawPagoApi);
}
