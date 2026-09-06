/**
 * Task 8.7 (Red) — contract test for `services/pagos.api.ts`.
 *
 * Fixes the contract of `obtenerHistorial(arrendamientoActivoId, token)`
 * and `iniciarPago(pagoId, token)` BEFORE the implementation exists, same
 * TDD convention as the other `arrendamiento-app` services.
 *
 * Contract (per `backend/pagos/infrastructure/api/{router,schemas}.py`):
 *   - `obtenerHistorial(arrendamientoActivoId, token)` — `GET
 *     /arrendamientos/{id}/pagos`. Maps `{ pagos: [...] }` (each
 *     snake_case) to `Pago[]` (camelCase).
 *   - `iniciarPago(pagoId, token)` — `POST /pagos/{pagoId}/iniciar`. Maps
 *     the single returned `Pago`.
 */
import { iniciarPago, obtenerHistorial, PagosApiError } from '../pagos.api';
import type { Pago } from '../pagos.api';

const token = 'header.payload.signature';

function mockJsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

const rawPago = {
  id: 'pago-uuid-1',
  arrendamiento_activo_id: 'arrendamiento-uuid-1',
  estado: 'pendiente',
  monto: 1_500_000,
  fecha_limite: '2026-10-05',
  fecha_pago: null,
  referencia_externa: null,
};

const mappedPago: Pago = {
  id: 'pago-uuid-1',
  arrendamientoActivoId: 'arrendamiento-uuid-1',
  estado: 'pendiente',
  monto: 1_500_000,
  fechaLimite: '2026-10-05',
  fechaPago: null,
  referenciaExterna: null,
};

describe('pagos.api (Red — frontend-flujo-arrendamiento)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('obtenerHistorial sends GET /arrendamientos/{id}/pagos and maps every Pago', async () => {
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ pagos: [rawPago] }));

    const result = await obtenerHistorial('arrendamiento-uuid-1', token);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/arrendamientos/arrendamiento-uuid-1/pagos'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: `Bearer ${token}` }),
      }),
    );
    expect(result).toEqual([mappedPago]);
  });

  it('obtenerHistorial throws PagosApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'No autorizado' }, false, 401));

    await expect(obtenerHistorial('arrendamiento-uuid-1', token)).rejects.toThrow(PagosApiError);
  });

  it('iniciarPago sends POST /pagos/{pagoId}/iniciar and maps the returned Pago', async () => {
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ ...rawPago, estado: 'completado' }));

    const result = await iniciarPago('pago-uuid-1', token);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/pagos/pago-uuid-1/iniciar'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: `Bearer ${token}` }),
      }),
    );
    expect(result).toEqual({ ...mappedPago, estado: 'completado' });
  });

  it('iniciarPago throws PagosApiError on a non-2xx response', async () => {
    jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(mockJsonResponse({ detail: 'Pago ya completado.' }, false, 409));

    await expect(iniciarPago('pago-uuid-1', token)).rejects.toThrow('Pago ya completado.');
  });
});
