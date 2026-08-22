"""`iniciar_relacion` use case.

Orchestrates the "Relación agencia-propietario iniciada por el propietario"
requirement of `openspec/changes/hu-007/specs/agencias/spec.md` (task 3.10,
4.4 of `openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.ports import RelacionRepositoryPort
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario


@dataclass
class IniciarRelacionCommand:
    agencia_id: uuid.UUID
    propietario_id: uuid.UUID


async def iniciar_relacion(
    command: IniciarRelacionCommand,
    *,
    relacion_repository: RelacionRepositoryPort,
) -> RelacionAgenciaPropietario:
    """Create a `RelacionAgenciaPropietario` pendiente for this propietario/agencia pair."""
    relacion = RelacionAgenciaPropietario.crear(
        agencia_id=command.agencia_id, propietario_id=command.propietario_id
    )
    return await relacion_repository.guardar(relacion)
