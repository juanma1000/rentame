"""`solicitar_ingreso` use case.

Orchestrates the "Ingreso a una agencia existente requiere aprobación" and
"Cardinalidad de membresía agente-agencia" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md` (tasks 3.3-3.4, 4.2 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.exceptions import AgenteYaTieneAgencia
from agencias.domain.ports import SolicitudIngresoRepositoryPort, UsuarioAgenciaRepositoryPort
from agencias.domain.solicitud_ingreso import SolicitudIngreso


@dataclass
class SolicitarIngresoCommand:
    agencia_id: uuid.UUID
    agente_id: uuid.UUID


async def solicitar_ingreso(
    command: SolicitarIngresoCommand,
    *,
    solicitud_repository: SolicitudIngresoRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
) -> SolicitudIngreso:
    """Create a `SolicitudIngreso` pendiente for `command.agente_id`.

    Raises `AgenteYaTieneAgencia` when `command.agente_id` already belongs
    to an agencia — in that case no solicitud is persisted.
    """
    if await usuario_repository.obtener_agencia_id(command.agente_id) is not None:
        raise AgenteYaTieneAgencia(f"El agente {command.agente_id} ya pertenece a una agencia")

    solicitud = SolicitudIngreso.crear(agencia_id=command.agencia_id, agente_id=command.agente_id)
    return await solicitud_repository.guardar(solicitud)
