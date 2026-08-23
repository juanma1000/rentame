"""`listar_inmuebles_publicos` use case.

Orchestrates the "GET /inmuebles/publicos" requirement described in
`design.md` decisión 1 of `openspec/changes/hu-003/` (tasks 1.1-1.2 of
`openspec/changes/hu-003/tasks.md`).

Same thin pass-through pattern already used by `listar_mis_inmuebles`/
`listar_inmuebles_gestionados`: no filters exist yet (per design.md's
"Non-Goals"), so this function takes no positional/command argument and
delegates directly to `InmuebleRepositoryPort.listar_disponibles`, which
already guarantees `estado == EstadoInmueble.DISPONIBLE` at the query level
(design.md decisión 2) — this use case must not re-filter or re-implement
that check.
"""

from __future__ import annotations

from inmuebles.domain.inmueble import Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort


async def listar_inmuebles_publicos(
    *,
    repository: InmuebleRepositoryPort,
) -> list[Inmueble]:
    """Return every `Inmueble` in estado `disponible` (empty list if none)."""
    return await repository.listar_disponibles()
