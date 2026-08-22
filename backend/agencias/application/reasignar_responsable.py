"""`reasignar_responsable` use case.

Orchestrates the "Agente responsable reasignable" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md` (tasks 3.17-3.18, 4.7 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia, RelacionNoEncontrada
from agencias.domain.ports import RelacionRepositoryPort, UsuarioAgenciaRepositoryPort
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario


@dataclass
class ReasignarResponsableCommand:
    relacion_id: uuid.UUID
    solicitante_id: uuid.UUID
    nuevo_agente_id: uuid.UUID


async def reasignar_responsable(
    command: ReasignarResponsableCommand,
    *,
    relacion_repository: RelacionRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
) -> RelacionAgenciaPropietario:
    """Reassign the `agente_responsable_id` of `command.relacion_id`.

    Raises `RelacionNoEncontrada` when `command.relacion_id` does not exist,
    and `AgenteNoEsMiembroDeAgencia` when either `command.solicitante_id`
    (the acting agente) or `command.nuevo_agente_id` is not a member of the
    relación's agencia — in that case the relación is not mutated.
    """
    relacion = await relacion_repository.obtener_por_id(command.relacion_id)
    if relacion is None:
        raise RelacionNoEncontrada(f"Relación {command.relacion_id} no existe")

    solicitante_agencia_id = await usuario_repository.obtener_agencia_id(command.solicitante_id)
    if solicitante_agencia_id != relacion.agencia_id:
        raise AgenteNoEsMiembroDeAgencia(
            f"El agente {command.solicitante_id} no es miembro de la agencia "
            f"{relacion.agencia_id}"
        )

    nuevo_agente_agencia_id = await usuario_repository.obtener_agencia_id(command.nuevo_agente_id)
    if nuevo_agente_agencia_id != relacion.agencia_id:
        raise AgenteNoEsMiembroDeAgencia(
            f"El agente {command.nuevo_agente_id} no es miembro de la agencia "
            f"{relacion.agencia_id}"
        )

    relacion.reasignar_responsable(command.nuevo_agente_id)
    return await relacion_repository.actualizar(relacion)
