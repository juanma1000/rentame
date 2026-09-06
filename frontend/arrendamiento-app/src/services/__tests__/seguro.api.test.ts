/**
 * Task 8.3 (Red) — contract test for `services/seguro.api.ts`.
 *
 * Fixes the contract of `obtenerEstado(token)` and
 * `contratarSeguro(cedula, documentos, token)` BEFORE the implementation
 * exists, same TDD convention as `identidad.api.test.ts`.
 *
 * Contract (per
 * `backend/seguro_arrendamiento/infrastructure/api/{router,schemas}.py`):
 *   - `obtenerEstado(token)` — `GET /seguro-arrendamiento/estado`. Maps
 *     `{ estado, prima_mensual }` to `EstadoSeguro` (`primaMensual`).
 *   - `contratarSeguro(cedula, documentos, token)` — sends a
 *     `multipart/form-data` POST to `/seguro-arrendamiento/contratar` with
 *     `cedula` (the backend's command requires it — same field the
 *     identidad step already collected) and repeated `documentos` file
 *     parts.
 *   - Both throw a typed `SeguroApiError` on a non-2xx response.
 */
import { contratarSeguro, obtenerEstado, SeguroApiError } from '../seguro.api';
import type { EstadoSeguro, PolizaArrendamiento } from '../seguro.api';

function makeFile(name: string): File {
  return new File(['fake-doc-bytes'], name, { type: 'application/pdf' });
}

const token = 'header.payload.signature';

function mockJsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe('seguro.api (Red — frontend-flujo-arrendamiento)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('obtenerEstado sends GET /seguro-arrendamiento/estado and maps prima_mensual', async () => {
    const estado = { estado: 'aprobada', prima_mensual: 45000 };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(estado));

    const result: EstadoSeguro = await obtenerEstado(token);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/seguro-arrendamiento/estado'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: `Bearer ${token}` }),
      }),
    );
    expect(result).toEqual({ estado: 'aprobada', primaMensual: 45000 });
  });

  it('obtenerEstado throws SeguroApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'No autorizado' }, false, 401));

    await expect(obtenerEstado(token)).rejects.toThrow(SeguroApiError);
  });

  it('contratarSeguro sends a multipart POST with cedula and repeated documentos', async () => {
    const poliza = {
      id: 'poliza-uuid-1',
      estado: 'pendiente',
      prima_mensual: null,
      referencia_externa: 'ref-1',
    };
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse(poliza));

    const doc1 = makeFile('desprendible.pdf');
    const doc2 = makeFile('certificado.pdf');

    const result: PolizaArrendamiento = await contratarSeguro('123456789', [doc1, doc2], token);

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/seguro-arrendamiento/contratar');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>).Authorization).toBe(`Bearer ${token}`);

    const form = init.body as FormData;
    expect(form.get('cedula')).toBe('123456789');
    expect(form.getAll('documentos')).toEqual([doc1, doc2]);

    expect(result).toEqual({
      id: 'poliza-uuid-1',
      estado: 'pendiente',
      primaMensual: null,
      referenciaExterna: 'ref-1',
    });
  });

  it('contratarSeguro throws SeguroApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(
        mockJsonResponse({ detail: 'Identidad no verificada.' }, false, 403),
      );

    await expect(
      contratarSeguro('123456789', [makeFile('a.pdf')], token),
    ).rejects.toThrow('Identidad no verificada.');
  });
});
