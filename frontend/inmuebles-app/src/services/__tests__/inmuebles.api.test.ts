/**
 * Task 16 (Red) — contract test for `services/inmuebles.api.ts`.
 *
 * Fixes the contract of `publicarInmueble(datos, fotos, token)` BEFORE the
 * implementation exists (TDD Red phase, delegated to qa-expert per
 * `openspec/config.yaml`'s `apply` rule).
 *
 * Contract (per `design.md` decision 1 and
 * `backend/inmuebles/infrastructure/api/router.py::crear_inmueble`):
 *   - Sends a `multipart/form-data` POST to `.../inmuebles/` (native `fetch`,
 *     no `axios` — there is no `axios` dependency anywhere in this monorepo
 *     yet, so `fetch` + `jest.spyOn(global, 'fetch')` is used instead, per
 *     the task instructions' "no precedent -> use fetch" rule).
 *   - Sets `Authorization: Bearer <token>`.
 *   - The `FormData` body carries the exact field names the backend's
 *     `Form(...)` parameters expect (snake_case: `area_m2`, `valor_mensual`),
 *     even though the TypeScript-facing `PublicarInmuebleInput` type uses
 *     camelCase (`areaM2`, `valorMensual`) per `frontend-standards.md`'s
 *     naming convention. Every photo is appended under the repeated `fotos`
 *     field, in the order provided.
 *   - On a successful (2xx) response, resolves with the parsed JSON body
 *     (the created `Inmueble`).
 *   - On a non-2xx response, throws an `InmueblesApiError` (typed, not a
 *     bare `Error`) whose `.message` is the backend's `{"detail": "..."}`
 *     message and whose `.status` is the HTTP status code.
 *
 * This module does not exist yet — every test below is expected to fail on
 * import (`Cannot find module '../inmuebles.api'`), which is the genuine Red
 * failure for this phase. No implementation is written here.
 */
import type {
  EditarInmuebleInput,
  Inmueble,
  InmueblePublico,
  InmueblePublicoDetalle,
  PublicarInmuebleInput,
} from '../inmuebles.api';
import {
  cambiarDisponibilidad,
  editarInmueble,
  InmueblesApiError,
  listarInmueblesGestionados,
  listarMisInmuebles,
  listarPublicos,
  obtenerPublico,
  publicarInmueble,
} from '../inmuebles.api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const validInput: PublicarInmuebleInput = {
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 65,
  habitaciones: 2,
  banos: 1,
  valorMensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
};

function makeFile(name: string): File {
  return new File(['fake-image-bytes'], name, { type: 'image/jpeg' });
}

const oneFoto = [makeFile('foto-1.jpg')];
const token = 'header.payload.signature';

const createdInmueble: Inmueble = {
  id: 'inmueble-uuid-1',
  propietarioId: 'propietario-uuid-1',
  direccion: validInput.direccion,
  barrio: validInput.barrio,
  ciudad: validInput.ciudad,
  tipo: validInput.tipo,
  areaM2: validInput.areaM2,
  habitaciones: validInput.habitaciones,
  banos: validInput.banos,
  valorMensual: validInput.valorMensual,
  descripcion: validInput.descripcion,
  estado: 'disponible',
  fotos: [
    {
      urlStorage: 'https://storage.local/foto-1.jpg',
      storageKey: 'inmueble-uuid-1/foto-1.jpg',
      orden: 0,
      esPrincipal: true,
    },
  ],
};

/**
 * Raw snake_case shape the backend actually sends in its JSON response.
 * Used as the mock `fetch` body — `publicarInmueble` maps this to
 * `createdInmueble` before returning.  Bug confirmed via curl against
 * http://localhost:8000/inmuebles/mios (see commit message for details).
 */
const rawCreatedInmueble = {
  id: 'inmueble-uuid-1',
  propietario_id: 'propietario-uuid-1',
  direccion: validInput.direccion,
  barrio: validInput.barrio,
  ciudad: validInput.ciudad,
  tipo: validInput.tipo,
  area_m2: validInput.areaM2,
  habitaciones: validInput.habitaciones,
  banos: validInput.banos,
  valor_mensual: validInput.valorMensual,
  descripcion: validInput.descripcion,
  estado: 'disponible',
  fotos: [
    {
      url_storage: 'https://storage.local/foto-1.jpg',
      storage_key: 'inmueble-uuid-1/foto-1.jpg',
      orden: 0,
      es_principal: true,
    },
  ],
};

function mockFetchResolvedOnce(body: unknown, status = 201): jest.SpyInstance {
  return jest.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

// ---------------------------------------------------------------------------

describe('inmuebles.api — publicarInmueble (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a POST request to an .../inmuebles/ endpoint with the Authorization bearer header', async () => {
    mockFetchResolvedOnce(rawCreatedInmueble);

    await publicarInmueble(validInput, oneFoto, token);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];

    expect(url).toEqual(expect.stringMatching(/\/inmuebles\/?$/));
    expect(requestInit.method).toBe('POST');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
  });

  it('sends the form fields with the exact snake_case names the backend expects, plus repeated "fotos" entries', async () => {
    mockFetchResolvedOnce(rawCreatedInmueble);

    const twoFotos = [makeFile('foto-1.jpg'), makeFile('foto-2.jpg')];
    await publicarInmueble(validInput, twoFotos, token);

    const [, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    const body = requestInit.body as FormData;

    expect(body).toBeInstanceOf(FormData);
    expect(body.get('direccion')).toBe(validInput.direccion);
    expect(body.get('barrio')).toBe(validInput.barrio);
    expect(body.get('ciudad')).toBe(validInput.ciudad);
    expect(body.get('tipo')).toBe(validInput.tipo);
    expect(body.get('area_m2')).toBe(String(validInput.areaM2));
    expect(body.get('habitaciones')).toBe(String(validInput.habitaciones));
    expect(body.get('banos')).toBe(String(validInput.banos));
    expect(body.get('valor_mensual')).toBe(String(validInput.valorMensual));
    expect(body.get('descripcion')).toBe(validInput.descripcion);

    const fotosEntries = body.getAll('fotos');
    expect(fotosEntries).toHaveLength(2);
    expect((fotosEntries[0] as File).name).toBe('foto-1.jpg');
    expect((fotosEntries[1] as File).name).toBe('foto-2.jpg');
  });

  it('resolves with the created inmueble parsed from a successful (201) response', async () => {
    mockFetchResolvedOnce(rawCreatedInmueble, 201);

    const result = await publicarInmueble(validInput, oneFoto, token);

    expect(result).toEqual(createdInmueble);
  });

  it('throws a typed InmueblesApiError with the backend detail message on a validation failure (422)', async () => {
    // NOTE: the two sequential assertions each call `publicarInmueble` once,
    // so fetch must be mocked persistently (not `Once`) to serve both calls.
    // Using `mockResolvedValueOnce` here would exhaust the queue on the first
    // call; the second call would then fall through to the stub (which rejects
    // with a TypeError), causing the second assertion to fail.
    jest.spyOn(global, 'fetch').mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'Se requiere al menos 1 foto.' }),
    } as Response);

    await expect(publicarInmueble(validInput, [], token)).rejects.toThrow(InmueblesApiError);
    await expect(publicarInmueble(validInput, [], token)).rejects.toThrow(
      'Se requiere al menos 1 foto.',
    );
  });

  it('exposes the HTTP status code on the thrown InmueblesApiError', async () => {
    mockFetchResolvedOnce({ detail: 'No autorizado.' }, 403);

    let caught: unknown;
    try {
      await publicarInmueble(validInput, oneFoto, token);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).status).toBe(403);
  });
});

// ---------------------------------------------------------------------------
// Task 17 (Red) — contract test for `editarInmueble`.
//
// Fixes the contract of `editarInmueble(inmuebleId, datos, token)` BEFORE the
// implementation exists (TDD Red phase), per the "Edición de inmueble
// publicado" requirement in `openspec/changes/hu-001/specs/inmuebles/spec.md`
// and `backend/inmuebles/infrastructure/api/router.py::editar_inmueble_endpoint`
// / `schemas.py::InmuebleEditRequest`.
//
// Contract:
//   - Sends a JSON (NOT multipart — editing never touches photos, per
//     `InmuebleEditRequest`'s docstring) `PUT` request to
//     `.../inmuebles/{inmuebleId}` (native `fetch`, same client as
//     `publicarInmueble`, no `axios`).
//   - Sets `Content-Type: application/json` and
//     `Authorization: Bearer <token>`.
//   - The JSON body carries the exact field names `InmuebleEditRequest`
//     expects (snake_case: `area_m2`, `valor_mensual`), mapped from the
//     camelCase-facing `EditarInmuebleInput` (identical shape to
//     `PublicarInmuebleInput` minus `fotos`, which this endpoint never
//     accepts).
//   - On a successful (2xx) response, resolves with the parsed JSON body
//     (the updated `Inmueble`).
//   - On a non-2xx response (422 validation, 403 not-owner, 404 not-found),
//     throws the same typed `InmueblesApiError` as `publicarInmueble`
//     (`.message` = backend's `detail`, `.status` = HTTP status code).
//
// `editarInmueble` does not exist yet in `../inmuebles.api` — every test
// below is expected to fail on import
// (`TypeError: (0 , inmuebles_api_1.editarInmueble) is not a function` /
// `Cannot find name 'editarInmueble'` at compile time), the genuine Red
// failure for this phase. No implementation is written here.
// ---------------------------------------------------------------------------

const editInput: EditarInmuebleInput = {
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 70,
  habitaciones: 3,
  banos: 2,
  valorMensual: 1_800_000,
  descripcion: 'Apartamento remodelado, ahora con balcón.',
};

const inmuebleId = 'inmueble-uuid-1';

const editedInmueble: Inmueble = {
  id: inmuebleId,
  propietarioId: 'propietario-uuid-1',
  direccion: editInput.direccion,
  barrio: editInput.barrio,
  ciudad: editInput.ciudad,
  tipo: editInput.tipo,
  areaM2: editInput.areaM2,
  habitaciones: editInput.habitaciones,
  banos: editInput.banos,
  valorMensual: editInput.valorMensual,
  descripcion: editInput.descripcion,
  estado: 'disponible',
  fotos: [],
};

/** Raw snake_case backend response for editarInmueble — maps to editedInmueble. */
const rawEditedInmueble = {
  id: inmuebleId,
  propietario_id: 'propietario-uuid-1',
  direccion: editInput.direccion,
  barrio: editInput.barrio,
  ciudad: editInput.ciudad,
  tipo: editInput.tipo,
  area_m2: editInput.areaM2,
  habitaciones: editInput.habitaciones,
  banos: editInput.banos,
  valor_mensual: editInput.valorMensual,
  descripcion: editInput.descripcion,
  estado: 'disponible',
  fotos: [],
};

describe('inmuebles.api — editarInmueble (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a PUT request to .../inmuebles/{id} with JSON content-type and the Authorization bearer header', async () => {
    mockFetchResolvedOnce(rawEditedInmueble, 200);

    await editarInmueble(inmuebleId, editInput, token);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];

    expect(url).toEqual(expect.stringMatching(new RegExp(`/inmuebles/${inmuebleId}$`)));
    expect(requestInit.method).toBe('PUT');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
    expect(headers['Content-Type']).toBe('application/json');
    expect(requestInit.body).not.toBeInstanceOf(FormData);
  });

  it('sends the JSON body with the exact snake_case field names InmuebleEditRequest expects', async () => {
    mockFetchResolvedOnce(rawEditedInmueble, 200);

    await editarInmueble(inmuebleId, editInput, token);

    const [, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(requestInit.body as string) as Record<string, unknown>;

    expect(body).toEqual({
      direccion: editInput.direccion,
      barrio: editInput.barrio,
      ciudad: editInput.ciudad,
      tipo: editInput.tipo,
      area_m2: editInput.areaM2,
      habitaciones: editInput.habitaciones,
      banos: editInput.banos,
      valor_mensual: editInput.valorMensual,
      descripcion: editInput.descripcion,
    });
  });

  it('resolves with the updated inmueble parsed from a successful (200) response', async () => {
    mockFetchResolvedOnce(rawEditedInmueble, 200);

    const result = await editarInmueble(inmuebleId, editInput, token);

    expect(result).toEqual(editedInmueble);
  });

  it('throws a typed InmueblesApiError with the backend detail message when editing an inmueble owned by another propietario (403)', async () => {
    mockFetchResolvedOnce({ detail: 'No tienes permisos sobre este inmueble.' }, 403);

    let caught: unknown;
    try {
      await editarInmueble(inmuebleId, editInput, token);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).message).toBe('No tienes permisos sobre este inmueble.');
    expect((caught as InmueblesApiError).status).toBe(403);
  });

  it('throws a typed InmueblesApiError when the inmueble does not exist (404)', async () => {
    // NOTE: the two sequential assertions each call `editarInmueble` once, so
    // fetch must be mocked persistently (not `Once`) to serve both calls —
    // same reasoning documented in the `publicarInmueble` 422 test above.
    jest.spyOn(global, 'fetch').mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Inmueble no encontrado.' }),
    } as Response);

    await expect(editarInmueble(inmuebleId, editInput, token)).rejects.toThrow(InmueblesApiError);
    await expect(editarInmueble('otro-id-inexistente', editInput, token)).rejects.toThrow(
      'Inmueble no encontrado.',
    );
  });
});

// ---------------------------------------------------------------------------
// Tasks 18/19 (Red) — contract tests for `listarMisInmuebles` and
// `cambiarDisponibilidad`.
//
// Fixes the contract of both functions BEFORE the implementation exists
// (TDD Red phase), per the "Despublicación temporal del inmueble" and
// "Listado de inmuebles propios" requirements in
// `openspec/changes/hu-001/specs/inmuebles/spec.md` and
// `backend/inmuebles/infrastructure/api/router.py`
// (`listar_mis_inmuebles_endpoint`, `cambiar_disponibilidad_endpoint`) /
// `schemas.py` (`CambiarDisponibilidadRequest`).
//
// Contract — `listarMisInmuebles(token)`:
//   - Sends a `GET` request to `.../inmuebles/mios` (native `fetch`, same
//     client as the functions above, no `axios`).
//   - Sets `Authorization: Bearer <token>`. No request body.
//   - On a successful (2xx) response, resolves with the parsed JSON array of
//     `Inmueble` (empty array when the propietario has none).
//   - On a non-2xx response, throws the same typed `InmueblesApiError` as
//     the other functions (`.message` = backend's `detail`, `.status` = HTTP
//     status code).
//
// Contract — `cambiarDisponibilidad(inmuebleId, nuevoEstado, token)`:
//   - Sends a JSON `PATCH` request to `.../inmuebles/{inmuebleId}/disponibilidad`.
//   - Sets `Content-Type: application/json` and
//     `Authorization: Bearer <token>`.
//   - The JSON body is `{"nuevo_estado": nuevoEstado}` exactly, where
//     `nuevoEstado` is `'disponible' | 'oculto'` (the two states reachable
//     through this HTTP endpoint per `CambiarDisponibilidadRequest`;
//     `'no_disponible'` is out of scope — reached only by a future internal
//     caller, never via HTTP).
//   - On a successful (2xx) response, resolves with the parsed JSON body
//     (the updated `Inmueble`).
//   - On a non-2xx response (403 not-owner, 404 not-found), throws the same
//     typed `InmueblesApiError` as the other functions.
//
// Neither `listarMisInmuebles` nor `cambiarDisponibilidad` exist yet in
// `../inmuebles.api` — every test below is expected to fail on import
// (`Cannot find name 'listarMisInmuebles'` / `'cambiarDisponibilidad'` at
// compile time, or `TypeError: ... is not a function` at runtime), the
// genuine Red failure for this phase. No implementation is written here.
// ---------------------------------------------------------------------------

const inmuebleDisponible: Inmueble = {
  id: 'inmueble-uuid-1',
  propietarioId: 'propietario-uuid-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 65,
  habitaciones: 2,
  banos: 1,
  valorMensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
  estado: 'disponible',
  fotos: [],
};

const inmuebleOculto: Inmueble = {
  ...inmuebleDisponible,
  id: 'inmueble-uuid-2',
  estado: 'oculto',
};

/** Raw snake_case backend response for listarMisInmuebles / cambiarDisponibilidad. */
const rawInmuebleDisponible = {
  id: 'inmueble-uuid-1',
  propietario_id: 'propietario-uuid-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  area_m2: 65,
  habitaciones: 2,
  banos: 1,
  valor_mensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
  estado: 'disponible',
  fotos: [],
};

const rawInmuebleOculto = {
  ...rawInmuebleDisponible,
  id: 'inmueble-uuid-2',
  estado: 'oculto',
};

describe('inmuebles.api — listarMisInmuebles (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a GET request to .../inmuebles/mios with the Authorization bearer header', async () => {
    mockFetchResolvedOnce([rawInmuebleDisponible, rawInmuebleOculto], 200);

    await listarMisInmuebles(token);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit | undefined,
    ];

    expect(url).toEqual(expect.stringMatching(/\/inmuebles\/mios$/));
    expect(requestInit?.method).toBe('GET');
    const headers = requestInit?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
  });

  it('resolves with the array of inmuebles parsed from a successful (200) response', async () => {
    mockFetchResolvedOnce([rawInmuebleDisponible, rawInmuebleOculto], 200);

    const result = await listarMisInmuebles(token);

    expect(result).toEqual([inmuebleDisponible, inmuebleOculto]);
  });

  it('resolves with an empty array when the propietario has no inmuebles published', async () => {
    mockFetchResolvedOnce([], 200);

    const result = await listarMisInmuebles(token);

    expect(result).toEqual([]);
  });

  it('throws a typed InmueblesApiError with the backend detail message on a failed response', async () => {
    mockFetchResolvedOnce({ detail: 'No autorizado.' }, 401);

    let caught: unknown;
    try {
      await listarMisInmuebles(token);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).message).toBe('No autorizado.');
    expect((caught as InmueblesApiError).status).toBe(401);
  });
});

describe('inmuebles.api — cambiarDisponibilidad (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a PATCH request to .../inmuebles/{id}/disponibilidad with JSON content-type and the Authorization bearer header', async () => {
    mockFetchResolvedOnce({ ...rawInmuebleDisponible, estado: 'oculto' }, 200);

    await cambiarDisponibilidad(inmuebleDisponible.id, 'oculto', token);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];

    expect(url).toEqual(
      expect.stringMatching(new RegExp(`/inmuebles/${inmuebleDisponible.id}/disponibilidad$`)),
    );
    expect(requestInit.method).toBe('PATCH');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
    expect(headers['Content-Type']).toBe('application/json');
  });

  it('sends the JSON body as {"nuevo_estado": "oculto"} when despublicando (18.1)', async () => {
    mockFetchResolvedOnce({ ...rawInmuebleDisponible, estado: 'oculto' }, 200);

    await cambiarDisponibilidad(inmuebleDisponible.id, 'oculto', token);

    const [, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(requestInit.body as string) as Record<string, unknown>;

    expect(body).toEqual({ nuevo_estado: 'oculto' });
  });

  it('sends the JSON body as {"nuevo_estado": "disponible"} when republicando (18.2)', async () => {
    mockFetchResolvedOnce({ ...rawInmuebleOculto, estado: 'disponible' }, 200);

    await cambiarDisponibilidad(inmuebleOculto.id, 'disponible', token);

    const [, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(requestInit.body as string) as Record<string, unknown>;

    expect(body).toEqual({ nuevo_estado: 'disponible' });
  });

  it('resolves with the updated inmueble parsed from a successful (200) response', async () => {
    const rawUpdated = { ...rawInmuebleDisponible, estado: 'oculto' };
    const expectedUpdated = { ...inmuebleDisponible, estado: 'oculto' };
    mockFetchResolvedOnce(rawUpdated, 200);

    const result = await cambiarDisponibilidad(inmuebleDisponible.id, 'oculto', token);

    expect(result).toEqual(expectedUpdated);
  });

  it('throws a typed InmueblesApiError with the backend detail message when the inmueble is owned by another propietario (403)', async () => {
    mockFetchResolvedOnce({ detail: 'No tienes permisos sobre este inmueble.' }, 403);

    let caught: unknown;
    try {
      await cambiarDisponibilidad(inmuebleDisponible.id, 'oculto', token);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).message).toBe('No tienes permisos sobre este inmueble.');
    expect((caught as InmueblesApiError).status).toBe(403);
  });

  it('throws a typed InmueblesApiError when the inmueble does not exist (404)', async () => {
    mockFetchResolvedOnce({ detail: 'Inmueble no encontrado.' }, 404);

    await expect(
      cambiarDisponibilidad('inmueble-inexistente', 'oculto', token),
    ).rejects.toThrow(InmueblesApiError);
  });
});

// ---------------------------------------------------------------------------
// Task 12 (Red) — contract test for `listarInmueblesGestionados`.
//
// Fixes the contract of `listarInmueblesGestionados(token)` BEFORE the
// implementation exists (TDD Red phase), per the "Listado de inmuebles
// gestionados por agencia" requirement in
// `openspec/changes/hu-002/specs/inmuebles/spec.md` and
// `backend/inmuebles/infrastructure/api/router.py`
// (`listar_inmuebles_gestionados_endpoint`, `GET /inmuebles/gestionados`,
// agente-only, resolved from `feature/hu-002-backend`).
//
// Contract — `listarInmueblesGestionados(token)`:
//   - Sends a `GET` request to `.../inmuebles/gestionados` (native `fetch`,
//     same client and mapping pattern as `listarMisInmuebles`).
//   - Sets `Authorization: Bearer <token>`. No request body.
//   - On a successful (2xx) response, resolves with the parsed JSON array of
//     `Inmueble`, mapped from the backend's snake_case `InmuebleResponse`
//     shape via the same `mapInmuebleFromApi` used by every other listing
//     function (empty array when the agente's agencia manages no
//     inmuebles).
//   - On a non-2xx response, throws the same typed `InmueblesApiError` as
//     the other functions (`.message` = backend's `detail`, `.status` = HTTP
//     status code).
//
// `listarInmueblesGestionados` does not exist yet in `../inmuebles.api` —
// every test below is expected to fail on import
// (`Cannot find name 'listarInmueblesGestionados'` at compile time, or
// `TypeError: ... is not a function` at runtime), the genuine Red failure
// for this phase. No implementation is written here.
// ---------------------------------------------------------------------------

describe('inmuebles.api — listarInmueblesGestionados (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a GET request to .../inmuebles/gestionados with the Authorization bearer header', async () => {
    mockFetchResolvedOnce([rawInmuebleDisponible, rawInmuebleOculto], 200);

    await listarInmueblesGestionados(token);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit | undefined,
    ];

    expect(url).toEqual(expect.stringMatching(/\/inmuebles\/gestionados$/));
    expect(requestInit?.method).toBe('GET');
    const headers = requestInit?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
  });

  it('resolves with the array of inmuebles parsed from a successful (200) response', async () => {
    mockFetchResolvedOnce([rawInmuebleDisponible, rawInmuebleOculto], 200);

    const result = await listarInmueblesGestionados(token);

    expect(result).toEqual([inmuebleDisponible, inmuebleOculto]);
  });

  it('resolves with an empty array when the agente\'s agencia manages no inmuebles', async () => {
    mockFetchResolvedOnce([], 200);

    const result = await listarInmueblesGestionados(token);

    expect(result).toEqual([]);
  });

  it('throws a typed InmueblesApiError with the backend detail message on a failed response', async () => {
    mockFetchResolvedOnce({ detail: 'No autorizado.' }, 401);

    let caught: unknown;
    try {
      await listarInmueblesGestionados(token);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).message).toBe('No autorizado.');
    expect((caught as InmueblesApiError).status).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// HU-003 (Red) — contract tests for `listarPublicos` and `obtenerPublico`.
//
// Fixes the contract of both functions BEFORE the implementation exists
// (TDD Red phase), per the "Listado público de inmuebles disponibles" and
// "Detalle público de un inmueble disponible" requirements in
// `openspec/changes/hu-003/specs/inmuebles/spec.md` and
// `openspec/changes/hu-003/design.md` decision 4/5 (new public-only
// response schemas, `GET /inmuebles/publicos` and
// `GET /inmuebles/publicos/{id}`, neither requires `Authorization`).
//
// Contract — `listarPublicos()`:
//   - Sends a `GET` request to `.../inmuebles/publicos` (native `fetch`, same
//     client and mapping pattern as the other listing functions).
//   - Does NOT set an `Authorization` header (no token param at all — this
//     is a public, unauthenticated endpoint).
//   - On a successful (2xx) response, resolves with the parsed JSON array of
//     `InmueblePublico`, mapped from the backend's snake_case
//     `InmueblePublicoListItemResponse` shape (`foto_principal`, `direccion`,
//     `barrio`, `ciudad`, `valor_mensual`, `habitaciones`, `banos`) to
//     camelCase (`fotoPrincipal`, `valorMensual`) — `fotoPrincipal` may be
//     `null` when the inmueble has no photos yet.
//   - On a non-2xx response, throws the same typed `InmueblesApiError` as
//     the other functions.
//
// Contract — `obtenerPublico(id)`:
//   - Sends a `GET` request to `.../inmuebles/publicos/{id}`.
//   - Does NOT set an `Authorization` header.
//   - On a successful (2xx) response, resolves with the parsed JSON body
//     mapped to `InmueblePublicoDetalle` (camelCase: `areaM2`,
//     `valorMensual`; `fotos` mapped to `{ urlStorage, orden, esPrincipal }`
//     per photo, same field names as the private `FotoInmueble` shape).
//   - On a 404 (inmueble does not exist, or is `oculto`/`no_disponible`),
//     throws the typed `InmueblesApiError` with `.status === 404` — per
//     `design.md` decision 1, the backend never reveals which of the two
//     cases it is.
//
// Neither `listarPublicos` nor `obtenerPublico` exist yet in
// `../inmuebles.api` — every test below is expected to fail on import
// (`Cannot find name 'listarPublicos'` / `'obtenerPublico'` at compile time,
// or `TypeError: ... is not a function` at runtime), the genuine Red
// failure for this phase. No implementation is written here.
// ---------------------------------------------------------------------------

const inmueblePublicoConFoto: InmueblePublico = {
  id: 'inmueble-uuid-1',
  fotoPrincipal: 'https://storage.local/foto-1.jpg',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  valorMensual: 1_500_000,
  habitaciones: 2,
  banos: 1,
};

const inmueblePublicoSinFoto: InmueblePublico = {
  id: 'inmueble-uuid-2',
  fotoPrincipal: null,
  direccion: 'Carrera 50 # 10-20',
  barrio: 'Poblado',
  ciudad: 'Medellín',
  valorMensual: 2_000_000,
  habitaciones: 3,
  banos: 2,
};

/** Raw snake_case backend response for the `/inmuebles/publicos` listing. */
const rawInmueblePublicoConFoto = {
  id: 'inmueble-uuid-1',
  foto_principal: 'https://storage.local/foto-1.jpg',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  valor_mensual: 1_500_000,
  habitaciones: 2,
  banos: 1,
};

const rawInmueblePublicoSinFoto = {
  id: 'inmueble-uuid-2',
  foto_principal: null,
  direccion: 'Carrera 50 # 10-20',
  barrio: 'Poblado',
  ciudad: 'Medellín',
  valor_mensual: 2_000_000,
  habitaciones: 3,
  banos: 2,
};

describe('inmuebles.api — listarPublicos (contract, Red, HU-003)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a GET request to .../inmuebles/publicos without an Authorization header', async () => {
    mockFetchResolvedOnce([rawInmueblePublicoConFoto, rawInmueblePublicoSinFoto], 200);

    await listarPublicos();

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit | undefined,
    ];

    expect(url).toEqual(expect.stringMatching(/\/inmuebles\/publicos$/));
    expect(requestInit?.method).toBe('GET');
    const headers = (requestInit?.headers ?? {}) as Record<string, string>;
    expect(headers['Authorization']).toBeUndefined();
  });

  it('resolves with the array of InmueblePublico parsed and mapped to camelCase from a successful (200) response', async () => {
    mockFetchResolvedOnce([rawInmueblePublicoConFoto, rawInmueblePublicoSinFoto], 200);

    const result = await listarPublicos();

    expect(result).toEqual([inmueblePublicoConFoto, inmueblePublicoSinFoto]);
  });

  it('resolves with an empty array when there are no inmuebles disponibles', async () => {
    mockFetchResolvedOnce([], 200);

    const result = await listarPublicos();

    expect(result).toEqual([]);
  });

  it('preserves a null fotoPrincipal for an inmueble without photos', async () => {
    mockFetchResolvedOnce([rawInmueblePublicoSinFoto], 200);

    const result = await listarPublicos();

    expect(result[0]?.fotoPrincipal).toBeNull();
  });

  it('throws a typed InmueblesApiError with the backend detail message on a failed response', async () => {
    mockFetchResolvedOnce({ detail: 'Error interno.' }, 500);

    let caught: unknown;
    try {
      await listarPublicos();
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).message).toBe('Error interno.');
    expect((caught as InmueblesApiError).status).toBe(500);
  });
});

const inmueblePublicoDetalle: InmueblePublicoDetalle = {
  id: 'inmueble-uuid-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  areaM2: 65,
  habitaciones: 2,
  banos: 1,
  valorMensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
  fotos: [
    { urlStorage: 'https://storage.local/foto-1.jpg', orden: 0, esPrincipal: true },
    { urlStorage: 'https://storage.local/foto-2.jpg', orden: 1, esPrincipal: false },
  ],
};

/** Raw snake_case backend response for `/inmuebles/publicos/{id}`. */
const rawInmueblePublicoDetalle = {
  id: 'inmueble-uuid-1',
  direccion: 'Calle 10 # 20-30',
  barrio: 'Laureles',
  ciudad: 'Medellín',
  tipo: 'apartamento',
  area_m2: 65,
  habitaciones: 2,
  banos: 1,
  valor_mensual: 1_500_000,
  descripcion: 'Apartamento luminoso cerca al parque.',
  fotos: [
    { url_storage: 'https://storage.local/foto-1.jpg', orden: 0, es_principal: true },
    { url_storage: 'https://storage.local/foto-2.jpg', orden: 1, es_principal: false },
  ],
};

describe('inmuebles.api — obtenerPublico (contract, Red, HU-003)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a GET request to .../inmuebles/publicos/{id} without an Authorization header', async () => {
    mockFetchResolvedOnce(rawInmueblePublicoDetalle, 200);

    await obtenerPublico(inmueblePublicoDetalle.id);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit | undefined,
    ];

    expect(url).toEqual(
      expect.stringMatching(new RegExp(`/inmuebles/publicos/${inmueblePublicoDetalle.id}$`)),
    );
    expect(requestInit?.method).toBe('GET');
    const headers = (requestInit?.headers ?? {}) as Record<string, string>;
    expect(headers['Authorization']).toBeUndefined();
  });

  it('resolves with the InmueblePublicoDetalle mapped to camelCase, including all ordered fotos', async () => {
    mockFetchResolvedOnce(rawInmueblePublicoDetalle, 200);

    const result = await obtenerPublico(inmueblePublicoDetalle.id);

    expect(result).toEqual(inmueblePublicoDetalle);
  });

  it('throws a typed InmueblesApiError with status 404 when the inmueble does not exist or is not disponible', async () => {
    mockFetchResolvedOnce({ detail: 'Inmueble no encontrado.' }, 404);

    let caught: unknown;
    try {
      await obtenerPublico('inmueble-oculto-o-inexistente');
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(InmueblesApiError);
    expect((caught as InmueblesApiError).status).toBe(404);
  });
});
