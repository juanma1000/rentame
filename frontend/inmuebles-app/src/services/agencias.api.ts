/**
 * HTTP client for the `agencias` backend domain.
 *
 * Provides read access to the relaciones between an agencia and its
 * propietarios, used by `PublicarInmueblePage` when the session belongs to
 * an `agente` who needs to publish on behalf of a linked propietario.
 *
 * The base URL is read from the same `INMUEBLES_API_URL` environment variable
 * used by `inmuebles.api.ts`; it falls back to `http://localhost:8000`.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * camelCase mirror of `RelacionResponse` from
 * `backend/agencias/infrastructure/api/schemas.py`.
 *
 * Fields:
 *   id                  — UUID of the relación record
 *   agenciaId           — UUID of the agencia
 *   propietarioId       — UUID of the propietario user
 *   propietarioEmail    — email of the propietario (for display in the selector)
 *   estado              — current state: 'activa' | 'revocada' | 'pendiente'
 *   agenteResponsableId — UUID of the agente responsible, or null
 */
export interface PropietarioVinculado {
  id: string;
  agenciaId: string;
  propietarioId: string;
  propietarioEmail: string;
  estado: string;
  agenteResponsableId: string | null;
}

// ---------------------------------------------------------------------------
// Internal — raw API response shapes (snake_case, as the backend sends them)
// ---------------------------------------------------------------------------

interface RawRelacionApi {
  id: string;
  agencia_id: string;
  propietario_id: string;
  propietario_email: string;
  estado: string;
  agente_responsable_id: string | null;
}

function mapRelacionFromApi(raw: RawRelacionApi): PropietarioVinculado {
  return {
    id: raw.id,
    agenciaId: raw.agencia_id,
    propietarioId: raw.propietario_id,
    propietarioEmail: raw.propietario_email,
    estado: raw.estado,
    agenteResponsableId: raw.agente_responsable_id,
  };
}

// ---------------------------------------------------------------------------
// API base URL (shared convention with inmuebles.api.ts)
// ---------------------------------------------------------------------------

const BASE_URL = (
  (process.env.INMUEBLES_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '');

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * GET `/agencias/mia/propietarios` — returns the propietarios linked to the
 * agente's agencia with `estado === 'activa'`.
 *
 * The backend returns ALL relacionas regardless of `estado`; this function
 * filters to only `activa` records so callers never need to filter themselves.
 *
 * @param token — JWT access token for the `Authorization: Bearer` header
 * @returns array of `PropietarioVinculado` with `estado === 'activa'`
 * @throws {Error} when the server returns a non-2xx status
 */
export async function listarPropietariosVinculados(
  token: string,
): Promise<PropietarioVinculado[]> {
  const response = await fetch(`${BASE_URL}/agencias/mia/propietarios`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = (await response.json()) as { detail?: string };
    throw new Error(body.detail ?? 'Error al obtener propietarios vinculados');
  }

  const data = (await response.json()) as RawRelacionApi[];
  return data
    .map(mapRelacionFromApi)
    .filter((p) => p.estado === 'activa');
}
