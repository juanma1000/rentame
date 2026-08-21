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
/**
 * Maps a raw backend response object (snake_case) to the TypeScript
 * `Inmueble` interface (camelCase).
 *
 * The backend's `InmuebleResponse` / `FotoResponse` schemas use snake_case
 * field names (`area_m2`, `valor_mensual`, `propietario_id`, `url_storage`,
 * `storage_key`, `es_principal`).  The rest of the fields coincide in both
 * conventions and are copied verbatim.
 */
export declare function mapInmuebleFromApi(raw: RawInmuebleApi): Inmueble;
/**
 * Typed error thrown when the inmuebles API returns a non-2xx response.
 *
 * `.message`  — the `detail` string from the backend's error body.
 * `.status`   — the HTTP status code (e.g. 422, 403, 404).
 */
export declare class InmueblesApiError extends Error {
    readonly status: number;
    constructor(message: string, status: number);
}
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
export declare function publicarInmueble(datos: PublicarInmuebleInput, fotos: File[], token: string): Promise<Inmueble>;
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
export declare function editarInmueble(inmuebleId: string, datos: EditarInmuebleInput, token: string): Promise<Inmueble>;
/**
 * GET `/inmuebles/mios` — list all inmuebles owned by the authenticated
 * propietario.
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @returns array of `Inmueble` owned by the propietario (empty when none)
 * @throws {InmueblesApiError} when the server returns a non-2xx status
 */
export declare function listarMisInmuebles(token: string): Promise<Inmueble[]>;
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
export declare function cambiarDisponibilidad(inmuebleId: string, nuevoEstado: 'disponible' | 'oculto', token: string): Promise<Inmueble>;
export {};
