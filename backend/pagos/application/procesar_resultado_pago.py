"""`procesar_resultado_pago` use case, invoked by the
`POST /pagos/webhook` endpoint (task 7.4).

Orchestrates the "Resultado modelado como pago con estado propio"
requirement of `openspec/changes/pago-mensual-renta/specs/pagos/spec.md`
(task 5.1-5.2 of `openspec/changes/pago-mensual-renta/tasks.md`).

Only ever locates the `Pago` by `referencia_externa` (set by
`iniciar_pago`, either synchronously or via `registrar_intento`) and
delegates the actual state transition to `Pago` itself — `Pago.
marcar_completado`/`marcar_fallido` already guard against a duplicate
webhook delivery arriving after the pago is `completado` (raising
`pagos.domain.exceptions.PagoYaCompletado`, propagated unchanged to the
API layer).
"""

from __future__ import annotations

from pagos.domain.exceptions import PagoNoEncontrado
from pagos.domain.pago import Pago
from pagos.domain.ports import PagoRepositoryPort, ResultadoWebhookPago

_ESTADO_COMPLETADO = "completado"
_ESTADO_FALLIDO = "fallido"


async def procesar_resultado_pago(
    resultado: ResultadoWebhookPago,
    *,
    pago_repository: PagoRepositoryPort,
) -> Pago:
    """Apply a pasarela's resultado de cobro to the `Pago` it refers to
    (located via `resultado.referencia_externa`).

    Raises `PagoNoEncontrado` when no pago has that `referencia_externa`.

    `resultado.estado == "completado"`: marks the pago `completado`, with
    `fecha_pago` set (spec.md: "Pago completado exitosamente queda
    registrado").

    `resultado.estado == "fallido"`: marks the pago `fallido`, with no
    `fecha_pago` (spec.md: "Pago fallido queda registrado").
    """
    pago = await pago_repository.obtener_por_referencia_externa(resultado.referencia_externa)
    if pago is None:
        raise PagoNoEncontrado(
            f"No existe ningún Pago con referencia_externa={resultado.referencia_externa!r}"
        )

    if resultado.estado == _ESTADO_COMPLETADO:
        pago.marcar_completado(referencia_externa=resultado.referencia_externa)
    elif resultado.estado == _ESTADO_FALLIDO:
        pago.marcar_fallido(referencia_externa=resultado.referencia_externa)
    else:
        raise ValueError(f"Estado de resultado de pago desconocido: {resultado.estado!r}")

    return await pago_repository.actualizar(pago)
