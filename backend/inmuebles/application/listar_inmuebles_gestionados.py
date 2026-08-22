"""`listar_inmuebles_gestionados` use case.

Orchestrates the "GET /inmuebles/gestionados" requirement described in
`design.md` decisión 6 of `openspec/changes/hu-002/` (tasks 3.3-3.4, 4.3 of
`openspec/changes/hu-002/tasks.md`).

This use case is a thin pass-through, same as `listar_mis_inmuebles`: the
cross-domain resolution of "which propietarios does this agente's agencia
manage" happens in the API layer (`inmuebles/infrastructure/api/router.py`),
consulting `agencias` there — never here, per design.md decisión 1
(`inmuebles/application` must never import from `agencias`). This function
only receives the already-resolved `propietario_ids` and delegates the
lookup itself to `InmuebleRepositoryPort.listar_por_propietarios`.
"""

from __future__ import annotations

import uuid

from inmuebles.domain.inmueble import Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort


async def listar_inmuebles_gestionados(
    propietario_ids: list[uuid.UUID],
    *,
    repository: InmuebleRepositoryPort,
) -> list[Inmueble]:
    """Return every `Inmueble` owned by any id in `propietario_ids`.

    Returns an empty list when `propietario_ids` is empty (the repository
    is still called; a real `WHERE ... IN ()` also returns no rows).
    """
    return await repository.listar_por_propietarios(propietario_ids)
