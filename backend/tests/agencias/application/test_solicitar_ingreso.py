"""Unit tests for the `solicitar_ingreso` use case
(`agencias/application/solicitar_ingreso.py`).

Covers tasks 3.3-3.4 of `openspec/changes/hu-007/tasks.md`, the "Ingreso a
una agencia existente requiere aprobación" and "Cardinalidad de membresía
agente-agencia" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/solicitar_ingreso.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.2). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `SolicitarIngresoCommand`: a plain dataclass with `agencia_id: UUID`,
  `agente_id: UUID`.
- `solicitar_ingreso(command, *, solicitud_repository, usuario_repository) -> SolicitudIngreso`:
  an async function that:
  1. Raises `AgenteYaTieneAgencia` when
     `usuario_repository.obtener_agencia_id(command.agente_id)` is not
     `None` — without calling `solicitud_repository.guardar`.
  2. Otherwise builds `SolicitudIngreso.crear(agencia_id=..., agente_id=...)`
     (starts `PENDIENTE`, per the entity's own factory) and persists it via
     `solicitud_repository.guardar`.
"""

import uuid

import pytest
from agencias.application.solicitar_ingreso import SolicitarIngresoCommand, solicitar_ingreso

from agencias.domain.exceptions import AgenteYaTieneAgencia
from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso
from tests.agencias.application.conftest import (
    FakeSolicitudIngresoRepository,
    FakeUsuarioAgenciaRepository,
)


class TestSolicitarIngreso:
    async def test_should_create_solicitud_pendiente_when_agente_has_no_agencia(
        self,
        fake_solicitud_repository: FakeSolicitudIngresoRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, None)

        # Act
        solicitud = await solicitar_ingreso(
            SolicitarIngresoCommand(agencia_id=agencia_id, agente_id=agente_id),
            solicitud_repository=fake_solicitud_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert solicitud.id is not None
        assert solicitud.estado == EstadoSolicitudIngreso.PENDIENTE
        assert solicitud.agencia_id == agencia_id
        assert solicitud.agente_id == agente_id
        assert fake_solicitud_repository.guardar_calls == [solicitud]
        # not yet a member: approval is still pending
        assert await fake_usuario_repository.obtener_agencia_id(agente_id) is None


class TestSolicitarIngresoRejectsAgenteConAgencia:
    async def test_should_raise_agente_ya_tiene_agencia_when_agente_already_has_one(
        self,
        fake_solicitud_repository: FakeSolicitudIngresoRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, uuid.uuid4())

        # Act / Assert
        with pytest.raises(AgenteYaTieneAgencia):
            await solicitar_ingreso(
                SolicitarIngresoCommand(agencia_id=agencia_id, agente_id=agente_id),
                solicitud_repository=fake_solicitud_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert fake_solicitud_repository.guardar_calls == []
