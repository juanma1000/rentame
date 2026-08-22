"""Shared despublicación-cascade helper.

Used by both `confirmar_relacion` (auto-revoke branch) and
`revocar_relacion`, per `openspec/changes/hu-007/design.md` decisión 4: "La
cascada de despublicación vive en `agencias/application/`, no en
`inmuebles`" — this module is the single place that implements it, so
neither use case duplicates the logic.

Mechanism (design.md decisión 4, steps 1-3):
1. Resolve the revoked agencia's members via
   `UsuarioAgenciaRepositoryPort.listar_ids_por_agencia`.
2. List the propietario's inmuebles via
   `inmuebles.application.listar_mis_inmuebles` (received as an injected,
   named parameter by the callers — never imported and called directly here
   either, so the same fakes/spies used by the callers' tests keep working
   transparently through this helper).
3. For every inmueble whose `agente_id` is a member of that set, call
   `inmuebles.application.cambiar_disponibilidad(inmueble_id, OCULTO,
   propietario_id=None)`. Inmuebles with `agente_id=None`, or managed by an
   agente outside that set, are left untouched.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from agencias.domain.ports import UsuarioAgenciaRepositoryPort
from inmuebles.application.cambiar_disponibilidad import CambiarDisponibilidadCommand
from inmuebles.application.listar_mis_inmuebles import ListarMisInmueblesCommand
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort


class ListarMisInmueblesFn(Protocol):
    async def __call__(
        self, command: ListarMisInmueblesCommand, *, repository: InmuebleRepositoryPort
    ) -> list[Inmueble]: ...


class CambiarDisponibilidadFn(Protocol):
    async def __call__(
        self, command: CambiarDisponibilidadCommand, *, repository: InmuebleRepositoryPort
    ) -> Inmueble | None: ...


async def despublicar_inmuebles_de_agencia(
    *,
    agencia_id: uuid.UUID,
    propietario_id: uuid.UUID,
    usuario_repository: UsuarioAgenciaRepositoryPort,
    inmueble_repository: InmuebleRepositoryPort,
    listar_mis_inmuebles: ListarMisInmueblesFn,
    cambiar_disponibilidad: CambiarDisponibilidadFn,
) -> None:
    """Hide every inmueble of `propietario_id` managed by a member of `agencia_id`."""
    miembros_agencia = set(await usuario_repository.listar_ids_por_agencia(agencia_id))

    inmuebles = await listar_mis_inmuebles(
        ListarMisInmueblesCommand(propietario_id=propietario_id),
        repository=inmueble_repository,
    )

    for inmueble in inmuebles:
        if inmueble.agente_id is not None and inmueble.agente_id in miembros_agencia:
            assert inmueble.id is not None
            await cambiar_disponibilidad(
                CambiarDisponibilidadCommand(
                    inmueble_id=inmueble.id,
                    nuevo_estado=EstadoInmueble.OCULTO,
                    propietario_id=None,
                ),
                repository=inmueble_repository,
            )
