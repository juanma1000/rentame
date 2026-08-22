"""`revocar_relacion` use case.

Orchestrates the "Revocación de la relación agencia-propietario por el
propietario" requirement of `openspec/changes/hu-007/specs/agencias/spec.md`,
and the "Despublicación en cascada por revocación de agencia" requirement of
`openspec/changes/hu-007/specs/inmuebles/spec.md` (tasks 3.14-3.16, 4.6 of
`openspec/changes/hu-007/tasks.md`).

No agencia-side approval is required for the propietario to revoke (spec.md).
The despublicación cascade (design.md decisión 4) is delegated to
`agencias/application/_cascada_despublicacion.py`, the same helper used by
`confirmar_relacion`'s auto-revoke branch.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.application._cascada_despublicacion import (
    CambiarDisponibilidadFn,
    ListarMisInmueblesFn,
    despublicar_inmuebles_de_agencia,
)
from agencias.domain.exceptions import PropietarioInvalido, RelacionNoEncontrada
from agencias.domain.ports import RelacionRepositoryPort, UsuarioAgenciaRepositoryPort
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario
from inmuebles.application.cambiar_disponibilidad import (
    cambiar_disponibilidad as _cambiar_disponibilidad_real,
)
from inmuebles.application.listar_mis_inmuebles import (
    listar_mis_inmuebles as _listar_mis_inmuebles_real,
)
from inmuebles.domain.ports import InmuebleRepositoryPort


@dataclass
class RevocarRelacionCommand:
    relacion_id: uuid.UUID
    propietario_id: uuid.UUID


async def revocar_relacion(
    command: RevocarRelacionCommand,
    *,
    relacion_repository: RelacionRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
    inmueble_repository: InmuebleRepositoryPort,
    listar_mis_inmuebles: ListarMisInmueblesFn = _listar_mis_inmuebles_real,
    cambiar_disponibilidad: CambiarDisponibilidadFn = _cambiar_disponibilidad_real,
) -> RelacionAgenciaPropietario:
    """Revoke `command.relacion_id` and run the despublicación cascade.

    Raises `RelacionNoEncontrada` when `command.relacion_id` does not exist,
    and `PropietarioInvalido` when `command.propietario_id` does not match
    the relación's own `propietario_id` — in that case the relación is not
    mutated and no cascade is triggered. No agencia-side approval is
    checked — the propietario can always revoke their own relación.
    """
    relacion = await relacion_repository.obtener_por_id(command.relacion_id)
    if relacion is None:
        raise RelacionNoEncontrada(f"Relación {command.relacion_id} no existe")

    if relacion.propietario_id != command.propietario_id:
        raise PropietarioInvalido(
            f"El propietario {command.propietario_id} no es dueño de la relación "
            f"{command.relacion_id}"
        )

    relacion.revocar()
    relacion = await relacion_repository.actualizar(relacion)

    await despublicar_inmuebles_de_agencia(
        agencia_id=relacion.agencia_id,
        propietario_id=relacion.propietario_id,
        usuario_repository=usuario_repository,
        inmueble_repository=inmueble_repository,
        listar_mis_inmuebles=listar_mis_inmuebles,
        cambiar_disponibilidad=cambiar_disponibilidad,
    )

    return relacion
