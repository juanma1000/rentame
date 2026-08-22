"""`aprobar_ingreso` use case.

Orchestrates the "Ingreso a una agencia existente requiere aprobación"
requirement of `openspec/changes/hu-007/specs/agencias/spec.md` (tasks
3.5-3.6, 4.2 of `openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia, SolicitudNoEncontrada
from agencias.domain.ports import SolicitudIngresoRepositoryPort, UsuarioAgenciaRepositoryPort
from agencias.domain.solicitud_ingreso import SolicitudIngreso


@dataclass
class AprobarIngresoCommand:
    solicitud_id: uuid.UUID
    aprobador_id: uuid.UUID


async def aprobar_ingreso(
    command: AprobarIngresoCommand,
    *,
    solicitud_repository: SolicitudIngresoRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
) -> SolicitudIngreso:
    """Approve `command.solicitud_id` and link the solicitante to the agencia.

    Raises `SolicitudNoEncontrada` when `command.solicitud_id` does not
    exist, and `AgenteNoEsMiembroDeAgencia` when `command.aprobador_id` is
    not a member of the solicitud's agencia — in that case nothing is
    mutated.
    """
    solicitud = await solicitud_repository.obtener_por_id(command.solicitud_id)
    if solicitud is None:
        raise SolicitudNoEncontrada(f"Solicitud {command.solicitud_id} no existe")

    aprobador_agencia_id = await usuario_repository.obtener_agencia_id(command.aprobador_id)
    if aprobador_agencia_id != solicitud.agencia_id:
        raise AgenteNoEsMiembroDeAgencia(
            f"El agente {command.aprobador_id} no es miembro de la agencia "
            f"{solicitud.agencia_id}"
        )

    solicitud.aprobar()
    solicitud = await solicitud_repository.actualizar(solicitud)
    await usuario_repository.asignar_agencia(solicitud.agente_id, solicitud.agencia_id)

    return solicitud
