"""`crear_agencia` use case.

Orchestrates the "Creación de agencia" and "Cardinalidad de membresía
agente-agencia" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md` (tasks 3.1-3.2, 4.1 of
`openspec/changes/hu-007/tasks.md`).

This module only orchestrates: every creation-time invariant of `Agencia`
stays in `Agencia.crear` (never re-implemented here).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from agencias.domain.agencia import Agencia
from agencias.domain.exceptions import AgenteYaTieneAgencia
from agencias.domain.ports import AgenciaRepositoryPort, UsuarioAgenciaRepositoryPort


@dataclass
class CrearAgenciaCommand:
    razon_social: str
    nit: str
    agente_id: uuid.UUID


async def crear_agencia(
    command: CrearAgenciaCommand,
    *,
    agencia_repository: AgenciaRepositoryPort,
    usuario_repository: UsuarioAgenciaRepositoryPort,
) -> Agencia:
    """Create a new `Agencia` and link the creating agente as its first member.

    Raises `AgenteYaTieneAgencia` when `command.agente_id` already belongs
    to an agencia — in that case no `Agencia` is persisted.
    """
    if await usuario_repository.obtener_agencia_id(command.agente_id) is not None:
        raise AgenteYaTieneAgencia(f"El agente {command.agente_id} ya pertenece a una agencia")

    agencia = Agencia.crear(razon_social=command.razon_social, nit=command.nit)
    agencia = await agencia_repository.guardar(agencia)

    assert agencia.id is not None
    await usuario_repository.asignar_agencia(command.agente_id, agencia.id)

    return agencia
