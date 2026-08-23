"""`obtener_inmueble_publico` use case.

Orchestrates the "GET /inmuebles/publicos/{id}" requirement described in
`design.md` decisión 1 of `openspec/changes/hu-003/` (tasks 1.3-1.4 of
`openspec/changes/hu-003/tasks.md`).

No new repository method is needed for this use case (per design.md
decisión 1): it reuses `InmuebleRepositoryPort.obtener_por_id` and validates
`estado == EstadoInmueble.DISPONIBLE` itself, returning `None` (never
raising) both when the `Inmueble` does not exist and when it exists but is
not `disponible` — this use case must never leak the existence/data of a
non-`disponible` inmueble through its return value.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort


@dataclass
class ObtenerInmueblePublicoCommand:
    inmueble_id: UUID


async def obtener_inmueble_publico(
    command: ObtenerInmueblePublicoCommand,
    *,
    repository: InmuebleRepositoryPort,
) -> Inmueble | None:
    """Return the `Inmueble` matching `command.inmueble_id` only when it
    exists AND is `disponible`; `None` otherwise (unknown id, `oculto` or
    `no_disponible`).
    """
    inmueble = await repository.obtener_por_id(command.inmueble_id)
    if inmueble is None or inmueble.estado != EstadoInmueble.DISPONIBLE:
        return None
    return inmueble
