/**
 * HTTP client for the `firma-contrato` backend domain, consumed by the
 * arrendamiento wizard's paso 3 (`GenerarContratoPage`).
 *
 * Same conventions as `identidad.api.ts`/`seguro.api.ts`: native `fetch`,
 * camelCase<->snake_case mapping, base URL from an env var with a
 * localhost fallback, a typed `*ApiError` on non-2xx responses.
 *
 * Deviation from tasks.md's literal `generarContrato(nombrePropietario)`
 * signature: `POST /firma-contrato/generar`'s `GenerarContratoRequest`
 * (`backend/firma_contrato/infrastructure/api/schemas.py`) requires
 * `inmueble_id`, `nombre_inquilino`, `direccion_inmueble`, `canon_mensual`
 * and `duracion_meses` in addition to `nombre_propietario` — none of which
 * the domain can synthesize on its own (the JWT only carries `sub`/`rol`,
 * no name; `Contrato` is the first place an `inmueble` enters this flow at
 * all, per design.md's Context section). `generarContrato` therefore takes
 * the full `GenerarContratoInput` object: `inmuebleId`/`direccionInmueble`/
 * `canonMensual` are threaded down from the inmueble the wizard was entered
 * from (see `ArrendamientoRoutes`'s props), `nombreInquilino`/
 * `nombrePropietario` are collected in `GenerarContratoPage`'s form, and
 * `duracionMeses` defaults to 12 (also editable in the form).
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * The estados the wizard's paso 3 can observe. `'no_iniciado'` is a
 * synthetic API-layer value (design.md decisión 6) for "no Contrato exists
 * yet".
 */
export type EstadoFirmaValue =
  | 'no_iniciado'
  | 'borrador'
  | 'enviado_a_firma'
  | 'firmado'
  | 'rechazado'
  | 'expirado';

export interface EstadoFirma {
  estado: EstadoFirmaValue;
  arrendamientoActivoId: string | null;
}

export interface Contrato {
  id: string;
  estado: string;
  referenciaExterna: string | null;
}

export interface GenerarContratoInput {
  inmuebleId: string;
  nombreInquilino: string;
  nombrePropietario: string;
  direccionInmueble: string;
  canonMensual: number;
  duracionMeses: number;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawEstadoFirmaApi {
  estado: string;
  arrendamiento_activo_id: string | null;
}

interface RawContratoApi {
  id: string;
  estado: string;
  referencia_externa: string | null;
}

function mapEstadoFromApi(raw: RawEstadoFirmaApi): EstadoFirma {
  return {
    estado: raw.estado as EstadoFirmaValue,
    arrendamientoActivoId: raw.arrendamiento_activo_id ?? null,
  };
}

function mapContratoFromApi(raw: RawContratoApi): Contrato {
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
 * Typed error thrown when the firma-contrato API returns a non-2xx
 * response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 401, 403, 422).
 */
export class FirmaApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'FirmaApiError';
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
 * GET `/firma-contrato/estado` — the authenticated inquilino's current
 * firma-contrato estado (`no_iniciado` when no `Contrato` exists yet).
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @throws {FirmaApiError} when the server returns a non-2xx status
 */
export async function obtenerEstado(token: string): Promise<EstadoFirma> {
  const response = await fetch(`${BASE_URL}/firma-contrato/estado`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new FirmaApiError(await readErrorDetail(response), response.status);
  }

  return mapEstadoFromApi((await response.json()) as RawEstadoFirmaApi);
}

/**
 * POST `/firma-contrato/generar` — request the generation of the contrato
 * de arrendamiento, given an approved `PolizaArrendamiento`.
 *
 * @param datos — full contrato data (see `GenerarContratoInput`)
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @returns the created `Contrato` parsed from the 200 JSON response
 * @throws {FirmaApiError} when the server returns a non-2xx status
 */
export async function generarContrato(
  datos: GenerarContratoInput,
  token: string,
): Promise<Contrato> {
  const body = JSON.stringify({
    inmueble_id: datos.inmuebleId,
    nombre_inquilino: datos.nombreInquilino,
    nombre_propietario: datos.nombrePropietario,
    direccion_inmueble: datos.direccionInmueble,
    canon_mensual: datos.canonMensual,
    duracion_meses: datos.duracionMeses,
  });

  const response = await fetch(`${BASE_URL}/firma-contrato/generar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body,
  });

  if (!response.ok) {
    throw new FirmaApiError(await readErrorDetail(response), response.status);
  }

  return mapContratoFromApi((await response.json()) as RawContratoApi);
}
