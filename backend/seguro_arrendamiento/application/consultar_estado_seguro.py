"""`consultar_estado_seguro` use case.

Orchestrates the "Consulta de estado de la póliza de seguro de
arrendamiento" requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/seguro-arrendamiento/spec.md`
(task 2.1-2.2 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`).

Purely a read over already-persisted `PolizaArrendamiento` records — never
calls `ProveedorSeguroArrendamientoPort`, never creates or modifies any
record (design.md decisión 2/6: `GET /seguro-arrendamiento/estado` is a
read-only endpoint for the wizard frontend to know which step it is on).

`ESTADO_NO_INICIADO` is a synthetic value of this API-facing layer, not a
member of
`seguro_arrendamiento.domain.poliza_arrendamiento.EstadoPoliza` — per
design.md decisión 6, it is inferred here from "no `PolizaArrendamiento`
exists for this usuario" rather than modeled as a new domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from seguro_arrendamiento.domain.ports import PolizaArrendamientoRepositoryPort

ESTADO_NO_INICIADO = "no_iniciado"


@dataclass
class EstadoSeguroResult:
    """Result of `consultar_estado_seguro`.

    `estado` is a plain `str` (not `EstadoPoliza`) since it can also hold
    the synthetic `ESTADO_NO_INICIADO` value, which is not a member of
    that enum. `prima_mensual` mirrors
    `PolizaArrendamiento.prima_mensual` — `None` unless the póliza has been
    `aprobada` (or beyond).
    """

    estado: str
    prima_mensual: float | None = None


async def consultar_estado_seguro(
    usuario_id: UUID,
    *,
    poliza_repository: PolizaArrendamientoRepositoryPort,
) -> EstadoSeguroResult:
    """Return the current seguro de arrendamiento estado for `usuario_id`.

    Returns `ESTADO_NO_INICIADO` (with `prima_mensual=None`) when
    `usuario_id` has no `PolizaArrendamiento` at all. Otherwise returns the
    `estado` and `prima_mensual` of the most recent póliza (highest
    `fecha`) — an account can have more than one attempt (a rejected one
    followed by an approved one), and only the latest one reflects the
    account's current standing.
    """
    polizas = await poliza_repository.listar_por_usuario(usuario_id)
    if not polizas:
        return EstadoSeguroResult(estado=ESTADO_NO_INICIADO, prima_mensual=None)

    mas_reciente = max(polizas, key=lambda poliza: poliza.fecha)
    return EstadoSeguroResult(
        estado=mas_reciente.estado.value,
        prima_mensual=mas_reciente.prima_mensual,
    )
