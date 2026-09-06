"""`procesar_resultado_firma` use case, invoked by the
`POST /firma-contrato/webhook` endpoint (task 6.4).

Orchestrates the "Contrato firmado crea un arrendamiento activo" and
"Póliza queda huérfana ante rechazo o expiración del contrato" requirements
of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(task 4.1-4.2 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

Per design.md decisión 4, a `rechazado`/`expirado` resultado never touches
the associated `PolizaArrendamiento` — this module has no dependency at
all on `seguro_arrendamiento` (not even the read-only
`PolizaArrendamientoPort`, which `generar_contrato` already used to gate
entry); the póliza is simply left as-is.
"""

from __future__ import annotations

from firma_contrato.domain.arrendamiento_activo import ArrendamientoActivo
from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.domain.exceptions import ContratoNoEncontrado, ContratoNoEnviadoAFirma
from firma_contrato.domain.ports import (
    ArrendamientoActivoRepositoryPort,
    ContratoRepositoryPort,
    ResultadoFirmaWebhook,
)

_ESTADO_FIRMADO = "firmado"
_ESTADO_RECHAZADO = "rechazado"
_ESTADO_EXPIRADO = "expirado"

__all__ = ["ContratoNoEncontrado", "procesar_resultado_firma"]


async def procesar_resultado_firma(
    resultado: ResultadoFirmaWebhook,
    *,
    contrato_repository: ContratoRepositoryPort,
    arrendamiento_repository: ArrendamientoActivoRepositoryPort,
) -> Contrato:
    """Apply a proveedor's resultado de firma to the `Contrato` it refers
    to (located via `resultado.referencia_externa`).

    Raises `ContratoNoEncontrado` when no contrato has that
    `referencia_externa`, and `ContratoNoEnviadoAFirma` when the located
    contrato is not currently in estado `enviado_a_firma` (a
    duplicate/out-of-order webhook delivery).

    `resultado.estado == "firmado"`: marks the contrato `firmado`,
    persists it, then creates the corresponding `ArrendamientoActivo` and
    persists it too (spec.md: "el sistema marca el contrato como firmado y
    crea un ArrendamientoActivo vinculado a ese contrato").

    `resultado.estado in ("rechazado", "expirado")`: marks the contrato
    with that estado and persists it — no `ArrendamientoActivo` is
    created, and the associated `PolizaArrendamiento` is never touched
    (spec.md: "La PolizaArrendamiento permanece en estado aprobada, sin
    ninguna cancelación automática").
    """
    contrato = await contrato_repository.obtener_por_referencia_externa(
        resultado.referencia_externa
    )
    if contrato is None:
        raise ContratoNoEncontrado(
            f"No existe ningún Contrato con referencia_externa={resultado.referencia_externa!r}"
        )
    if contrato.estado != EstadoContrato.ENVIADO_A_FIRMA:
        raise ContratoNoEnviadoAFirma(
            f"El contrato {contrato.id} no está en estado enviado_a_firma (estado actual: "
            f"{contrato.estado.value}); se ignora este resultado de firma"
        )

    if resultado.estado == _ESTADO_FIRMADO:
        contrato.marcar_firmado()
        contrato = await contrato_repository.actualizar(contrato)
        arrendamiento = ArrendamientoActivo.crear(contrato=contrato)
        await arrendamiento_repository.guardar(arrendamiento)
        return contrato

    if resultado.estado == _ESTADO_RECHAZADO:
        contrato.marcar_rechazado()
    elif resultado.estado == _ESTADO_EXPIRADO:
        contrato.marcar_expirado()
    else:
        raise ValueError(f"Estado de resultado de firma desconocido: {resultado.estado!r}")

    return await contrato_repository.actualizar(contrato)
