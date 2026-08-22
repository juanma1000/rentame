"""`confirmar_relacion` use case.

Orchestrates the "Relación agencia-propietario iniciada por el propietario"
and "Máximo una agencia activa por propietario" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md`, and the "Despublicación en
cascada por revocación de agencia" requirement of
`openspec/changes/hu-007/specs/inmuebles/spec.md` (tasks 3.11-3.13, 4.5 of
`openspec/changes/hu-007/tasks.md`).

Per design.md decisión 3, activating a new relación auto-revokes any other
`ACTIVA` relación the same propietario had, running the despublicación
cascade for the replaced agencia before activating the new one (decisión 4,
implemented in `agencias/application/_cascada_despublicacion.py`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.application._cascada_despublicacion import (
    CambiarDisponibilidadFn,
    ListarMisInmueblesFn,
    despublicar_inmuebles_de_agencia,
)
from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia, RelacionNoEncontrada
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
class ConfirmarRelacionCommand:
    relacion_id: uuid.UUID
    agente_id: uuid.UUID


async def confirmar_relacion(
    command: ConfirmarRelacionCommand,
    *,
    relacion_repository: RelacionRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
    inmueble_repository: InmuebleRepositoryPort,
    listar_mis_inmuebles: ListarMisInmueblesFn = _listar_mis_inmuebles_real,
    cambiar_disponibilidad: CambiarDisponibilidadFn = _cambiar_disponibilidad_real,
) -> RelacionAgenciaPropietario:
    """Activate `command.relacion_id` on behalf of an agencia member.

    Raises `RelacionNoEncontrada` when `command.relacion_id` does not exist,
    and `AgenteNoEsMiembroDeAgencia` when `command.agente_id` is not a
    member of the relación's agencia — in that case nothing is mutated and
    the despublicación cascade is never triggered.

    If the propietario already had another relación `ACTIVA`, it is
    auto-revoked and the despublicación cascade runs for its agencia
    (design.md decisión 3), before this relación is activated.
    """
    relacion = await relacion_repository.obtener_por_id(command.relacion_id)
    if relacion is None:
        raise RelacionNoEncontrada(f"Relación {command.relacion_id} no existe")

    agente_agencia_id = await usuario_repository.obtener_agencia_id(command.agente_id)
    if agente_agencia_id != relacion.agencia_id:
        raise AgenteNoEsMiembroDeAgencia(
            f"El agente {command.agente_id} no es miembro de la agencia {relacion.agencia_id}"
        )

    relacion_previa = await relacion_repository.obtener_activa_por_propietario(
        relacion.propietario_id
    )
    if relacion_previa is not None:
        relacion_previa.revocar()
        await relacion_repository.actualizar(relacion_previa)

        await despublicar_inmuebles_de_agencia(
            agencia_id=relacion_previa.agencia_id,
            propietario_id=relacion.propietario_id,
            usuario_repository=usuario_repository,
            inmueble_repository=inmueble_repository,
            listar_mis_inmuebles=listar_mis_inmuebles,
            cambiar_disponibilidad=cambiar_disponibilidad,
        )

    relacion.activar()
    return await relacion_repository.actualizar(relacion)
