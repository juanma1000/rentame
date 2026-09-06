"""`consultar_estado_identidad` use case.

Orchestrates the "Consulta de estado de validación de identidad"
requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/identidad/spec.md`
(task 1.1-1.2 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`).

Purely a read over already-persisted `ValidacionIdentidad` attempts — never
calls `ProveedorValidacionIdentidadPort`, never creates or modifies any
record (design.md decisión 2/6: `GET /identidad/estado` is a read-only
endpoint for the wizard frontend to know which step it is on).

`ESTADO_NO_INICIADO` is a synthetic value of this API-facing layer, not a
member of `identidad.domain.validacion_identidad.EstadoValidacion` — per
design.md decisión 6, it is inferred here from "no `ValidacionIdentidad`
exists for this usuario" rather than modeled as a new domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from identidad.domain.ports import ValidacionIdentidadRepositoryPort

ESTADO_NO_INICIADO = "no_iniciado"


@dataclass
class EstadoIdentidadResult:
    """Result of `consultar_estado_identidad`.

    `estado` is a plain `str` (not `EstadoValidacion`) since it can also
    hold the synthetic `ESTADO_NO_INICIADO` value, which is not a member of
    that enum.
    """

    estado: str


async def consultar_estado_identidad(
    usuario_id: UUID,
    *,
    validacion_repository: ValidacionIdentidadRepositoryPort,
) -> EstadoIdentidadResult:
    """Return the current identidad estado for `usuario_id`.

    Returns `ESTADO_NO_INICIADO` when `usuario_id` has no
    `ValidacionIdentidad` at all. Otherwise returns the `estado` of the
    most recent attempt (highest `fecha`) — an account can have more than
    one attempt (a rejected one followed by an approved one, per
    `ValidacionIdentidad.iniciar`'s invariant), and only the latest one
    reflects the account's current standing.
    """
    validaciones = await validacion_repository.listar_por_usuario(usuario_id)
    if not validaciones:
        return EstadoIdentidadResult(estado=ESTADO_NO_INICIADO)

    mas_reciente = max(validaciones, key=lambda validacion: validacion.fecha)
    return EstadoIdentidadResult(estado=mas_reciente.estado.value)
