"""`consultar_estado_firma` use case.

Orchestrates the "Consulta de estado del contrato y arrendamiento activo"
requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/firma-contrato/spec.md`
(task 3.1-3.2 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`).

Purely a read over already-persisted `Contrato`/`ArrendamientoActivo`
records — never calls `ProveedorFirmaElectronicaPort`, never creates or
modifies any record (design.md decisión 2/6: `GET /firma-contrato/estado`
is a read-only endpoint for the wizard frontend to know which step it is
on).

`ESTADO_NO_INICIADO` is a synthetic value of this API-facing layer, not a
member of `firma_contrato.domain.contrato.EstadoContrato` — per design.md
decisión 6, it is inferred here from "no `Contrato` exists for this
usuario" rather than modeled as a new domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from firma_contrato.domain.contrato import EstadoContrato
from firma_contrato.domain.ports import ArrendamientoActivoRepositoryPort, ContratoRepositoryPort

ESTADO_NO_INICIADO = "no_iniciado"


@dataclass
class EstadoFirmaResult:
    """Result of `consultar_estado_firma`.

    `estado` is a plain `str` (not `EstadoContrato`) since it can also
    hold the synthetic `ESTADO_NO_INICIADO` value, which is not a member
    of that enum. `arrendamiento_activo_id` is only populated when the
    most recent `Contrato` is `firmado`.
    """

    estado: str
    arrendamiento_activo_id: UUID | None = None


async def consultar_estado_firma(
    usuario_id: UUID,
    *,
    contrato_repository: ContratoRepositoryPort,
    arrendamiento_repository: ArrendamientoActivoRepositoryPort,
) -> EstadoFirmaResult:
    """Return the current firma-contrato estado for `usuario_id`.

    Returns `ESTADO_NO_INICIADO` when `usuario_id` has no `Contrato` at
    all. Otherwise returns the `estado` of the most recent contrato
    (highest `fecha`) — an account can have more than one contrato
    (rejected/expired attempts followed by a signed one), and only the
    latest one reflects the account's current standing. When that
    contrato is `firmado`, also resolves and returns the `id` of the
    `ArrendamientoActivo` it produced (via `contrato_id`, per
    `ArrendamientoActivo.crear`).
    """
    contratos = await contrato_repository.listar_por_usuario(usuario_id)
    if not contratos:
        return EstadoFirmaResult(estado=ESTADO_NO_INICIADO, arrendamiento_activo_id=None)

    mas_reciente = max(contratos, key=lambda contrato: contrato.fecha)

    arrendamiento_activo_id: UUID | None = None
    if mas_reciente.estado == EstadoContrato.FIRMADO:
        arrendamientos = await arrendamiento_repository.listar_por_usuario(usuario_id)
        for arrendamiento in arrendamientos:
            if arrendamiento.contrato_id == mas_reciente.id:
                arrendamiento_activo_id = arrendamiento.id
                break

    return EstadoFirmaResult(
        estado=mas_reciente.estado.value,
        arrendamiento_activo_id=arrendamiento_activo_id,
    )
