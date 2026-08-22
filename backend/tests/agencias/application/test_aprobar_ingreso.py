"""Unit tests for the `aprobar_ingreso` use case
(`agencias/application/aprobar_ingreso.py`).

Covers tasks 3.5-3.6 of `openspec/changes/hu-007/tasks.md`, the "Ingreso a
una agencia existente requiere aprobación" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/aprobar_ingreso.py` does not exist yet,
so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.2). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `AprobarIngresoCommand`: a plain dataclass with `solicitud_id: UUID`,
  `aprobador_id: UUID` (the agente performing the approval).
- `aprobar_ingreso(command, *, solicitud_repository, usuario_repository) -> SolicitudIngreso`:
  an async function that:
  1. Raises `SolicitudNoEncontrada` when `command.solicitud_id` does not
     exist (not covered by a dedicated task here, but required for the
     happy/rejection paths below to make sense).
  2. Raises `AgenteNoEsMiembroDeAgencia` when
     `usuario_repository.obtener_agencia_id(command.aprobador_id)` does not
     equal the solicitud's `agencia_id` — without mutating the solicitud or
     `usuario_repository`.
  3. Otherwise calls `solicitud.aprobar()` (entity transition to
     `APROBADA`), persists it via `solicitud_repository.actualizar`, and
     links the requesting agente via
     `usuario_repository.asignar_agencia(solicitud.agente_id, solicitud.agencia_id)`.
"""

import uuid

import pytest

from agencias.application.aprobar_ingreso import AprobarIngresoCommand, aprobar_ingreso
from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia
from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso, SolicitudIngreso
from tests.agencias.application.conftest import (
    FakeSolicitudIngresoRepository,
    FakeUsuarioAgenciaRepository,
)


class TestAprobarIngreso:
    async def test_should_approve_and_link_solicitante_when_approver_is_agencia_member(
        self,
        fake_solicitud_repository: FakeSolicitudIngresoRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_solicitante_id = uuid.uuid4()
        aprobador_id = uuid.uuid4()
        solicitud = fake_solicitud_repository.seed(
            SolicitudIngreso.crear(agencia_id=agencia_id, agente_id=agente_solicitante_id)
        )
        fake_usuario_repository.seed(aprobador_id, agencia_id)
        fake_usuario_repository.seed(agente_solicitante_id, None)

        # Act
        assert solicitud.id is not None
        result = await aprobar_ingreso(
            AprobarIngresoCommand(solicitud_id=solicitud.id, aprobador_id=aprobador_id),
            solicitud_repository=fake_solicitud_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert result.estado == EstadoSolicitudIngreso.APROBADA
        assert await fake_usuario_repository.obtener_agencia_id(agente_solicitante_id) == agencia_id


class TestAprobarIngresoRejectsNonMemberApprover:
    async def test_should_raise_agente_no_es_miembro_when_approver_is_not_agencia_member(
        self,
        fake_solicitud_repository: FakeSolicitudIngresoRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        otra_agencia_id = uuid.uuid4()
        agente_solicitante_id = uuid.uuid4()
        aprobador_id = uuid.uuid4()
        solicitud = fake_solicitud_repository.seed(
            SolicitudIngreso.crear(agencia_id=agencia_id, agente_id=agente_solicitante_id)
        )
        fake_usuario_repository.seed(aprobador_id, otra_agencia_id)
        fake_usuario_repository.seed(agente_solicitante_id, None)

        # Act / Assert
        assert solicitud.id is not None
        with pytest.raises(AgenteNoEsMiembroDeAgencia):
            await aprobar_ingreso(
                AprobarIngresoCommand(solicitud_id=solicitud.id, aprobador_id=aprobador_id),
                solicitud_repository=fake_solicitud_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert fake_solicitud_repository.actualizar_calls == []
        assert await fake_usuario_repository.obtener_agencia_id(agente_solicitante_id) is None
