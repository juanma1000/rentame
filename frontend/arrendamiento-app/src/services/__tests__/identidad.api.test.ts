/**
 * Task 8.1 (Red) — contract test for `services/identidad.api.ts`.
 *
 * Fixes the contract of `obtenerEstado(token)` and
 * `validarIdentidad(cedula, imagenFrente, imagenDorso, token)` BEFORE the
 * implementation exists, same TDD convention as
 * `inmuebles-app/src/services/__tests__/inmuebles.api.test.ts`.
 *
 * Contract (per `backend/identidad/infrastructure/api/{router,schemas}.py`):
 *   - `obtenerEstado(token)` — `GET /identidad/estado` with
 *     `Authorization: Bearer <token>`. Maps `{ estado }` (snake_case is
 *     identical to camelCase here — single field) to `EstadoIdentidad`.
 *   - `validarIdentidad(cedula, imagenFrente, imagenDorso, token)` — sends a
 *     `multipart/form-data` POST to `/identidad/validar` with fields
 *     `cedula`, `imagen_frente`, `imagen_dorso` (native `fetch`, no axios —
 *     same precedent as `inmuebles.api.ts`). Maps the response's
 *     `referencia_externa` to `referenciaExterna`.
 *   - Both throw a typed `IdentidadApiError` (not a bare `Error`) on a
 *     non-2xx response, carrying `.message` (backend's `detail`) and
 *     `.status`.
 */
import {
  IdentidadApiError,
  obtenerEstado,
  validarIdentidad,
} from '../identidad.api';
import type { EstadoIdentidad, ValidacionIdentidad } from '../identidad.api';

function makeFile(name: string): File {
  return new File(['fake-image-bytes'], name, { type: 'image/jpeg' });
}

const token = 'header.payload.signature';

function mockJsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe('identidad.api (Red — frontend-flujo-arrendamiento)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('obtenerEstado sends GET /identidad/estado with the bearer token and maps the response', async () => {
    const estado: EstadoIdentidad = { estado: 'no_iniciado' };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(estado));

    const result = await obtenerEstado(token);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/identidad/estado'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: `Bearer ${token}` }),
      }),
    );
    expect(result).toEqual({ estado: 'no_iniciado' });
  });

  it('obtenerEstado throws IdentidadApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'No autorizado' }, false, 401));

    await expect(obtenerEstado(token)).rejects.toThrow(IdentidadApiError);
  });

  it('validarIdentidad sends a multipart POST with cedula, imagen_frente and imagen_dorso', async () => {
    const validacion = { id: 'validacion-uuid-1', estado: 'pendiente', referencia_externa: 'ref-1' };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(validacion));

    const frente = makeFile('frente.jpg');
    const dorso = makeFile('dorso.jpg');

    const result: ValidacionIdentidad = await validarIdentidad('123456789', frente, dorso, token);

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/identidad/validar');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>).Authorization).toBe(`Bearer ${token}`);

    const form = init.body as FormData;
    expect(form.get('cedula')).toBe('123456789');
    expect(form.get('imagen_frente')).toBe(frente);
    expect(form.get('imagen_dorso')).toBe(dorso);

    expect(result).toEqual({
      id: 'validacion-uuid-1',
      estado: 'pendiente',
      referenciaExterna: 'ref-1',
    });
  });

  it('validarIdentidad throws IdentidadApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(
        mockJsonResponse({ detail: 'Identidad ya verificada.' }, false, 409),
      );

    await expect(
      validarIdentidad('123456789', makeFile('a.jpg'), makeFile('b.jpg'), token),
    ).rejects.toThrow('Identidad ya verificada.');
  });
});
