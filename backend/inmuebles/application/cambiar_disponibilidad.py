"""`cambiar_disponibilidad` use case.

Orchestrates the "Despublicación temporal del inmueble" and "Transición
automática a no disponible" requirements of
`openspec/changes/hu-001/specs/inmuebles/spec.md` (tasks 3.5-3.7, 4.3 of
`openspec/changes/hu-001/tasks.md`).

Per `design.md` decisión 4, this is a single, synchronous, idempotent
application method — not an event listener — reused both by the
propietario-facing despublicar/republicar flow (`propietario_id` set) and by
the future `arrendamiento` use case marking `NO_DISPONIBLE`
(`propietario_id=None`, no ownership concept for that caller).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from inmuebles.domain.exceptions import InmuebleNoEncontrado, PropietarioInvalido
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort

_TRANSICIONES = {
    EstadoInmueble.OCULTO: Inmueble.despublicar,
    EstadoInmueble.DISPONIBLE: Inmueble.republicar,
    EstadoInmueble.NO_DISPONIBLE: Inmueble.marcar_no_disponible,
}


@dataclass
class CambiarDisponibilidadCommand:
    """`propietario_id` is `None` for system/internal callers (e.g. the
    future `arrendamiento` use case), in which case ownership is NOT
    checked. When provided, it MUST match the loaded `Inmueble`'s owner."""

    inmueble_id: uuid.UUID
    nuevo_estado: EstadoInmueble
    propietario_id: uuid.UUID | None = None


async def cambiar_disponibilidad(
    command: CambiarDisponibilidadCommand,
    *,
    repository: InmuebleRepositoryPort,
) -> Inmueble:
    """Transition the `Inmueble`'s `estado` and persist it.

    Raises `InmuebleNoEncontrado` when `command.inmueble_id` does not exist,
    and `PropietarioInvalido` when `command.propietario_id` is not `None`
    and does not match the entity's owner. The actual transition logic is
    delegated to the corresponding `Inmueble` method — never reimplemented
    here.
    """
    inmueble = await repository.obtener_por_id(command.inmueble_id)
    if inmueble is None:
        raise InmuebleNoEncontrado(f"Inmueble {command.inmueble_id} no existe")
    if command.propietario_id is not None and inmueble.propietario_id != command.propietario_id:
        raise PropietarioInvalido(
            f"Propietario {command.propietario_id} no es dueño del inmueble "
            f"{command.inmueble_id}"
        )

    _TRANSICIONES[command.nuevo_estado](inmueble)

    return await repository.actualizar(inmueble)
