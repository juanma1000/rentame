"""`iniciar_pago` use case, invoked by the `POST /pagos/{id}/iniciar`
endpoint (task 7.2).

Orchestrates the "El inquilino inicia el pago (modelo pull)" and "Split
de pago ejecutado por la pasarela" requirements of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md` (task 4.1-4.2 of
`openspec/changes/pago-mensual-renta/tasks.md`).

This module only orchestrates: it locates the `Pago`, rejects up front
when it is already `completado` (never calling the pasarela in that
case), walks `ArrendamientoActivo` -> `PolizaArrendamiento`/`Inmueble` to
assemble the split, then delegates to `Pago` for the resulting state
transition — same pattern as `firma_contrato.application.generar_contrato`.
"""

from __future__ import annotations

from uuid import UUID

from pagos.domain.exceptions import (
    ArrendamientoActivoNoEncontrado,
    PagoNoEncontrado,
    PagoYaCompletado,
)
from pagos.domain.pago import EstadoPago, Pago
from pagos.domain.ports import (
    ArrendamientoActivoPort,
    InmueblePort,
    PagoRepositoryPort,
    PasarelaPagosPort,
    PolizaArrendamientoPort,
    SplitPago,
)

_ESTADO_COMPLETADO_PASARELA = "completado"


async def iniciar_pago(
    pago_id: UUID,
    *,
    pago_repository: PagoRepositoryPort,
    arrendamiento_activo: ArrendamientoActivoPort,
    poliza_arrendamiento: PolizaArrendamientoPort,
    inmueble: InmueblePort,
    pasarela: PasarelaPagosPort,
) -> Pago:
    """Run an iniciar-pago attempt for `pago_id`.

    Raises `PagoNoEncontrado` when no `Pago` matches `pago_id`.

    Raises `PagoYaCompletado` when the located `Pago` is already
    `completado` — `pasarela.iniciar_cobro` is never called in that case
    (spec.md: "Un pago ya completado no puede reiniciarse").

    Raises `ArrendamientoActivoNoEncontrado` when the `Pago`'s
    `ArrendamientoActivo` (or the póliza/inmueble data reachable from it)
    cannot be resolved — a referential-integrity condition that should
    not happen in practice.

    Otherwise assembles the split (monto total = `Pago.monto`, prima a
    retener = `PolizaArrendamiento.prima_mensual`, destino del neto =
    `Inmueble.propietario_id`), calls `pasarela.iniciar_cobro`, and:
    - marks the `Pago` `completado` when the pasarela resolves
      synchronously (`resultado.estado == "completado"`, `FakeAdapter`'s
      only possible value);
    - otherwise only records `resultado.referencia_externa` on the `Pago`
      (still `pendiente`), leaving the actual resolution to
      `pagos.application.procesar_resultado_pago` once the webhook
      reports it (Wompi's async flow).
    """
    pago = await pago_repository.obtener_por_id(pago_id)
    if pago is None:
        raise PagoNoEncontrado(f"No existe ningún Pago con id={pago_id}")
    if pago.estado == EstadoPago.COMPLETADO:
        raise PagoYaCompletado(f"El pago {pago.id} ya está completado y no puede reiniciarse")

    arrendamiento_info = await arrendamiento_activo.obtener(pago.arrendamiento_activo_id)
    if arrendamiento_info is None:
        raise ArrendamientoActivoNoEncontrado(
            f"No existe ningún ArrendamientoActivo con id={pago.arrendamiento_activo_id}"
        )

    prima_mensual = await poliza_arrendamiento.obtener_prima_mensual(arrendamiento_info.poliza_id)
    inmueble_info = await inmueble.obtener(arrendamiento_info.inmueble_id)
    if prima_mensual is None or inmueble_info is None:
        raise ArrendamientoActivoNoEncontrado(
            f"Datos incompletos para armar el split del pago {pago.id} "
            f"(arrendamiento_activo_id={arrendamiento_info.id})"
        )

    split = SplitPago(
        monto_total=pago.monto,
        monto_prima_retenida=prima_mensual,
        propietario_id=inmueble_info.propietario_id,
    )
    resultado = await pasarela.iniciar_cobro(split)

    if resultado.estado == _ESTADO_COMPLETADO_PASARELA:
        pago.marcar_completado(referencia_externa=resultado.referencia_externa)
    else:
        pago.registrar_intento(referencia_externa=resultado.referencia_externa)

    return await pago_repository.actualizar(pago)
