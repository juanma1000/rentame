"""`salir_de_agencia` use case.

Orchestrates the "Salida voluntaria de un agente" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md` (tasks 3.7-3.9, 4.3 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.exceptions import UltimoAgenteConRelacionesActivas
from agencias.domain.ports import RelacionRepositoryPort, UsuarioAgenciaRepositoryPort
from agencias.domain.relacion_agencia_propietario import EstadoRelacion


@dataclass
class SalirDeAgenciaCommand:
    agencia_id: uuid.UUID
    agente_id: uuid.UUID


async def salir_de_agencia(
    command: SalirDeAgenciaCommand,
    *,
    relacion_repository: RelacionRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
) -> None:
    """Remove `command.agente_id` from `command.agencia_id`.

    Raises `UltimoAgenteConRelacionesActivas` when `command.agente_id` is
    the only member of the agencia AND the agencia has at least one relación
    `ACTIVA` — in that case membership is not touched.
    """
    miembros = await usuario_repository.listar_ids_por_agencia(command.agencia_id)
    es_ultimo_miembro = miembros == [command.agente_id]

    if es_ultimo_miembro:
        relaciones = await relacion_repository.listar_por_agencia(command.agencia_id)
        tiene_relaciones_activas = any(
            relacion.estado == EstadoRelacion.ACTIVA for relacion in relaciones
        )
        if tiene_relaciones_activas:
            raise UltimoAgenteConRelacionesActivas(
                f"El agente {command.agente_id} es el último miembro de la agencia "
                f"{command.agencia_id}, que tiene relaciones activas"
            )

    await usuario_repository.remover_agencia(command.agente_id)
