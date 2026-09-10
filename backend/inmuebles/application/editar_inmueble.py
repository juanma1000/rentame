"""`editar_inmueble` use case.

Orchestrates the "Edición de inmueble publicado" requirement of
`openspec/changes/hu-001/specs/inmuebles/spec.md` (tasks 3.3-3.4, 4.2 of
`openspec/changes/hu-001/tasks.md`). Editing `fotos` is out of scope for
this use case.

Ownership is enforced here (design.md decisión 5): `command.propietario_id`
comes from the JWT, not from the entity, and must match the loaded
`Inmueble.propietario_id` before any field is applied or persisted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from inmuebles.domain.exceptions import InmuebleNoEncontrado, PropietarioInvalido
from inmuebles.domain.inmueble import Inmueble
from inmuebles.domain.ports import GeocodingPort, InmuebleRepositoryPort


@dataclass
class EditarInmuebleCommand:
    """Editable data fields for an existing `Inmueble`, plus the ids needed
    to locate it and authorize the caller."""

    inmueble_id: uuid.UUID
    propietario_id: uuid.UUID
    direccion: str
    barrio: str
    ciudad: str
    tipo: str
    area_m2: Decimal
    habitaciones: int
    banos: int
    valor_mensual: Decimal
    descripcion: str


async def editar_inmueble(
    command: EditarInmuebleCommand,
    *,
    repository: InmuebleRepositoryPort,
    geocoding: GeocodingPort,
) -> Inmueble:
    """Apply `command`'s data to the owned `Inmueble` and persist it.

    Raises `InmuebleNoEncontrado` when `command.inmueble_id` does not exist,
    `PropietarioInvalido` when `command.propietario_id` does not match the
    entity's owner, and `DomainValidationError` (via
    `Inmueble.actualizar_datos`) when `command`'s data violates a business
    invariant (e.g. `valor_mensual <= 0`) — in any of these cases
    `repository.actualizar` is never called.

    Re-geocodes via `geocoding` (vista-mapa-inmuebles-leaflet, design.md
    decisión 3) only when `direccion`, `barrio` or `ciudad` actually
    changed from the entity's current values — otherwise the existing
    `latitud`/`longitud` are left untouched and `geocoding` is never
    called, to avoid spending a request against a rate-limited provider on
    every edit. As with `publicar_inmueble`, `geocoding.geocodificar` never
    raises: a failed/empty lookup clears the coordinates to `None` rather
    than blocking the edit.
    """
    inmueble = await repository.obtener_por_id(command.inmueble_id)
    if inmueble is None:
        raise InmuebleNoEncontrado(f"Inmueble {command.inmueble_id} no existe")
    if inmueble.propietario_id != command.propietario_id:
        raise PropietarioInvalido(
            f"Propietario {command.propietario_id} no es dueño del inmueble "
            f"{command.inmueble_id}"
        )

    ubicacion_cambio = (
        inmueble.direccion != command.direccion
        or inmueble.barrio != command.barrio
        or inmueble.ciudad != command.ciudad
    )

    inmueble.actualizar_datos(
        direccion=command.direccion,
        barrio=command.barrio,
        ciudad=command.ciudad,
        tipo=command.tipo,
        area_m2=command.area_m2,
        habitaciones=command.habitaciones,
        banos=command.banos,
        valor_mensual=command.valor_mensual,
        descripcion=command.descripcion,
    )

    if ubicacion_cambio:
        coordenadas = await geocoding.geocodificar(
            direccion=command.direccion, barrio=command.barrio, ciudad=command.ciudad
        )
        inmueble.actualizar_coordenadas(
            coordenadas.latitud if coordenadas else None,
            coordenadas.longitud if coordenadas else None,
        )

    return await repository.actualizar(inmueble)
