/**
 * Task 8.5 (Red) — contract test for `services/firma.api.ts`.
 *
 * Fixes the contract of `obtenerEstado(token)` and
 * `generarContrato(datos, token)` BEFORE the implementation exists, same TDD
 * convention as `identidad.api.test.ts`/`seguro.api.test.ts`.
 *
 * Contract (per
 * `backend/firma_contrato/infrastructure/api/{router,schemas}.py`):
 *   - `obtenerEstado(token)` — `GET /firma-contrato/estado`. Maps
 *     `{ estado, arrendamiento_activo_id }` to `EstadoFirma`
 *     (`arrendamientoActivoId`).
 *   - `generarContrato(datos, token)` — sends a JSON POST to
 *     `/firma-contrato/generar` with the full `GenerarContratoRequest` shape
 *     the backend requires (`inmueble_id`, `nombre_inquilino`,
 *     `nombre_propietario`, `direccion_inmueble`, `canon_mensual`,
 *     `duracion_meses`).
 *
 *   Deviation from tasks.md's literal `generarContrato(nombrePropietario)`
 *   signature: the backend's `GenerarContratoCommand` requires 5 more
 *   fields the wizard already has from its entry context (inmueble) or
 *   collects in the form — see `GenerarContratoPage`'s own docstring for
 *   the full rationale. This service accepts the full input object instead
 *   of a single string.
 */
import { FirmaApiError, generarContrato, obtenerEstado } from '../firma.api';
import type { Contrato, EstadoFirma, GenerarContratoInput } from '../firma.api';

const token = 'header.payload.signature';

function mockJsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

const input: GenerarContratoInput = {
  inmuebleId: 'inmueble-uuid-1',
  nombreInquilino: 'Juan Pérez',
  nombrePropietario: 'María Gómez',
  direccionInmueble: 'Calle 10 # 20-30',
  canonMensual: 1_500_000,
  duracionMeses: 12,
};

describe('firma.api (Red — frontend-flujo-arrendamiento)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('obtenerEstado sends GET /firma-contrato/estado and maps arrendamiento_activo_id', async () => {
    const estado = { estado: 'firmado', arrendamiento_activo_id: 'arrendamiento-uuid-1' };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(estado));

    const result: EstadoFirma = await obtenerEstado(token);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/firma-contrato/estado'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: `Bearer ${token}` }),
      }),
    );
    expect(result).toEqual({
      estado: 'firmado',
      arrendamientoActivoId: 'arrendamiento-uuid-1',
    });
  });

  it('obtenerEstado throws FirmaApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'No autorizado' }, false, 401));

    await expect(obtenerEstado(token)).rejects.toThrow(FirmaApiError);
  });

  it('generarContrato sends a JSON POST with the full snake_case request body', async () => {
    const contrato = { id: 'contrato-uuid-1', estado: 'enviado_a_firma', referencia_externa: 'ref-1' };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(contrato));

    const result: Contrato = await generarContrato(input, token);

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/firma-contrato/generar');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>).Authorization).toBe(`Bearer ${token}`);
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');

    expect(JSON.parse(init.body as string)).toEqual({
      inmueble_id: input.inmuebleId,
      nombre_inquilino: input.nombreInquilino,
      nombre_propietario: input.nombrePropietario,
      direccion_inmueble: input.direccionInmueble,
      canon_mensual: input.canonMensual,
      duracion_meses: input.duracionMeses,
    });

    expect(result).toEqual({
      id: 'contrato-uuid-1',
      estado: 'enviado_a_firma',
      referenciaExterna: 'ref-1',
    });
  });

  it('generarContrato throws FirmaApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'Póliza no aprobada.' }, false, 403));

    await expect(generarContrato(input, token)).rejects.toThrow('Póliza no aprobada.');
  });
});
