"""`listar_mis_inmuebles` use case.

Orchestrates the "Listado de inmuebles propios" requirement of
`openspec/changes/hu-001/specs/inmuebles/spec.md` (tasks 3.8-3.9, 4.4 of
`openspec/changes/hu-001/tasks.md`).

This use case is a thin pass-through: filtering by owner is the
repository's responsibility (`InmuebleRepositoryPort.listar_por_propietario`),
not something reimplemented at this layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from inmuebles.domain.inmueble import Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort


@dataclass
class ListarMisInmueblesCommand:
    """`propietario_id` is extracted from the JWT (design.md decisión 5)."""

    propietario_id: uuid.UUID


async def listar_mis_inmuebles(
    command: ListarMisInmueblesCommand,
    *,
    repository: InmuebleRepositoryPort,
) -> list[Inmueble]:
    """Return every `Inmueble` owned by `command.propietario_id`."""
    return await repository.listar_por_propietario(command.propietario_id)
