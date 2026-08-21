/**
 * HTTP client for the `inmuebles` backend domain.
 *
 * Sends multipart/form-data requests to the Rentame backend and maps
 * between the camelCase TypeScript interface (`PublicarInmuebleInput`) and
 * the snake_case FormData field names the backend expects (see
 * `backend/inmuebles/infrastructure/api/schemas.py` and `router.py`).
 *
 * The base URL is read from the `INMUEBLES_API_URL` environment variable at
 * build time; it falls back to `http://localhost:8000` for local development.
 * Do NOT hard-code the host without this fallback.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PublicarInmuebleInput {
  direccion: string;
  barrio: string;
  ciudad: string;
  tipo: string;
  areaM2: number;
  habitaciones: number;
  banos: number;
  valorMensual: number;
  descripcion: string;
}

/**
 * Input type for editing an existing property listing.
 *
 * Identical in shape to `PublicarInmuebleInput` — same camelCase fields, same
 * types — but declared separately to keep the editing contract explicit.
 * Photo management is intentionally excluded: `PUT /inmuebles/{id}` accepts
 * only text data (`InmuebleEditRequest` has no `fotos` field).
 */
export type EditarInmuebleInput = PublicarInmuebleInput;

export interface FotoInmueble {
  urlStorage: string;
  storageKey: string;
  orden: number;
  esPrincipal: boolean;
}

export interface Inmueble {
  id: string;
  propietarioId: string;
  direccion: string;
  barrio: string;
  ciudad: string;
  tipo: string;
  areaM2: number;
  habitaciones: number;
  banos: number;
  valorMensual: number;
  descripcion: string;
  estado: string;
  fotos: FotoInmueble[];
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawFotoApi {
  url_storage: string;
  storage_key: string;
  orden: number;
  es_principal: boolean;
}

interface RawInmuebleApi {
  id: string;
  propietario_id: string;
  direccion: string;
  barrio: string;
  ciudad: string;
  tipo: string;
  area_m2: number;
  habitaciones: number;
  banos: number;
  valor_mensual: number;
  descripcion: string;
  estado: string;
  fotos: RawFotoApi[];
}

function mapFotoFromApi(raw: RawFotoApi): FotoInmueble {
  return {
    urlStorage: raw.url_storage,
    storageKey: raw.storage_key,
    orden: raw.orden,
    esPrincipal: raw.es_principal,
  };
}

/**
 * Maps a raw backend response object (snake_case) to the TypeScript
 * `Inmueble` interface (camelCase).
 *
 * The backend's `InmuebleResponse` / `FotoResponse` schemas use snake_case
 * field names (`area_m2`, `valor_mensual`, `propietario_id`, `url_storage`,
 * `storage_key`, `es_principal`).  The rest of the fields coincide in both
 * conventions and are copied verbatim.
 */
export function mapInmuebleFromApi(raw: RawInmuebleApi): Inmueble {
  return {
    id: String(raw.id),
    propietarioId: String(raw.propietario_id),
    direccion: raw.direccion,
    barrio: raw.barrio,
    ciudad: raw.ciudad,
    tipo: raw.tipo,
    areaM2: raw.area_m2,
    habitaciones: raw.habitaciones,
    banos: raw.banos,
    valorMensual: raw.valor_mensual,
    descripcion: raw.descripcion,
    estado: raw.estado,
    fotos: (raw.fotos ?? []).map(mapFotoFromApi),
  };
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the inmuebles API returns a non-2xx response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 422, 403, 404).
 */
export class InmueblesApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'InmueblesApiError';
    this.status = status;
    // Maintain correct instanceof chain when transpiled to ES5/CJS.
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

const BASE_URL = (
  (process.env.INMUEBLES_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '');

/**
 * POST `/inmuebles/` — publish a new property listing with photos.
 *
 * Sends multipart/form-data using the native `fetch` API.  The TypeScript
 * interface uses camelCase; the FormData fields use the snake_case names
 * the FastAPI backend declares as `Form(...)` parameters.
 *
 * @param datos   — property data in camelCase (`PublicarInmuebleInput`)
 * @param fotos   — 1 to 10 `File` objects (JPEG/PNG images)
 * @param token   — JWT access token for the `Authorization: Bearer` header
 * @returns the created `Inmueble` parsed from the 201 JSON response
 * @throws {InmueblesApiError} when the server returns a non-2xx status
 */
export async function publicarInmueble(
  datos: PublicarInmuebleInput,
  fotos: File[],
  token: string,
): Promise<Inmueble> {
  const form = new FormData();

  // Text fields — same name in TS and on the wire.
  form.append('direccion', datos.direccion);
  form.append('barrio', datos.barrio);
  form.append('ciudad', datos.ciudad);
  form.append('tipo', datos.tipo);
  form.append('descripcion', datos.descripcion);

  // Numeric fields — camelCase → snake_case, serialized as strings.
  form.append('area_m2', String(datos.areaM2));
  form.append('habitaciones', String(datos.habitaciones));
  form.append('banos', String(datos.banos));
  form.append('valor_mensual', String(datos.valorMensual));

  // Photos — repeated `fotos` entries, in order.
  for (const foto of fotos) {
    form.append('fotos', foto);
  }

  const response = await fetch(`${BASE_URL}/inmuebles/`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new InmueblesApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return mapInmuebleFromApi((await response.json()) as RawInmuebleApi);
}

/**
 * PUT `/inmuebles/{inmuebleId}` — update the text data of an existing listing.
 *
 * Sends a JSON body using the native `fetch` API.  The TypeScript interface
 * uses camelCase (`EditarInmuebleInput`); the JSON body uses the snake_case
 * names `InmuebleEditRequest` declares.  Photos are never touched by this
 * endpoint.
 *
 * @param inmuebleId — UUID of the inmueble to edit
 * @param datos      — updated property data in camelCase (`EditarInmuebleInput`)
 * @param token      — JWT access token for the `Authorization: Bearer` header
 * @returns the updated `Inmueble` parsed from the 200 JSON response
 * @throws {InmueblesApiError} when the server returns a non-2xx status
 */
export async function editarInmueble(
  inmuebleId: string,
  datos: EditarInmuebleInput,
  token: string,
): Promise<Inmueble> {
  const body = JSON.stringify({
    direccion: datos.direccion,
    barrio: datos.barrio,
    ciudad: datos.ciudad,
    tipo: datos.tipo,
    area_m2: datos.areaM2,
    habitaciones: datos.habitaciones,
    banos: datos.banos,
    valor_mensual: datos.valorMensual,
    descripcion: datos.descripcion,
  });

  const response = await fetch(`${BASE_URL}/inmuebles/${inmuebleId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body,
  });

  if (!response.ok) {
    const errorBody = (await response.json()) as { detail?: string };
    throw new InmueblesApiError(errorBody.detail ?? 'Error desconocido', response.status);
  }

  return mapInmuebleFromApi((await response.json()) as RawInmuebleApi);
}

/**
 * GET `/inmuebles/mios` — list all inmuebles owned by the authenticated
 * propietario.
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @returns array of `Inmueble` owned by the propietario (empty when none)
 * @throws {InmueblesApiError} when the server returns a non-2xx status
 */
export async function listarMisInmuebles(token: string): Promise<Inmueble[]> {
  const response = await fetch(`${BASE_URL}/inmuebles/mios`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new InmueblesApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return ((await response.json()) as RawInmuebleApi[]).map(mapInmuebleFromApi);
}

/**
 * PATCH `/inmuebles/{inmuebleId}/disponibilidad` — toggle the availability
 * state of an existing listing.
 *
 * Only the two states reachable via HTTP are accepted here: `'disponible'`
 * (republicar) and `'oculto'` (despublicar). The `'no_disponible'` state is
 * set exclusively by an internal future caller (arrendamiento domain) — never
 * through this endpoint.
 *
 * @param inmuebleId  — UUID of the inmueble to update
 * @param nuevoEstado — target state: `'disponible'` or `'oculto'`
 * @param token       — JWT access token for the `Authorization: Bearer` header
 * @returns the updated `Inmueble` parsed from the 200 JSON response
 * @throws {InmueblesApiError} when the server returns a non-2xx status
 */
export async function cambiarDisponibilidad(
  inmuebleId: string,
  nuevoEstado: 'disponible' | 'oculto',
  token: string,
): Promise<Inmueble> {
  const response = await fetch(`${BASE_URL}/inmuebles/${inmuebleId}/disponibilidad`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ nuevo_estado: nuevoEstado }),
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new InmueblesApiError(body.detail ?? 'Error desconocido', response.status);
  }

  return mapInmuebleFromApi((await response.json()) as RawInmuebleApi);
}
