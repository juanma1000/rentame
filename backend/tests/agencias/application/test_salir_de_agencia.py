"""Unit tests for the `salir_de_agencia` use case
(`agencias/application/salir_de_agencia.py`).

Covers tasks 3.7-3.9 of `openspec/changes/hu-007/tasks.md`, the "Salida
voluntaria de un agente" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/salir_de_agencia.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.3). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `SalirDeAgenciaCommand`: a plain dataclass with `agencia_id: UUID`,
  `agente_id: UUID`.
- `salir_de_agencia(command, *, relacion_repository, usuario_repository) -> None`:
  an async function that:
  1. Reads the agencia's current membership via
     `usuario_repository.listar_ids_por_agencia(command.agencia_id)`.
  2. When `command.agente_id` is the ONLY member AND
     `relacion_repository.listar_por_agencia(command.agencia_id)` contains
     at least one relación in `EstadoRelacion.ACTIVA`, raises
     `UltimoAgenteConRelacionesActivas` — without calling
     `usuario_repository.remover_agencia`.
  3. Otherwise (more than one member, OR the last member but with no
     `ACTIVA` relaciones) calls
     `usuario_repository.remover_agencia(command.agente_id)`.
"""

import uuid

import pytest
from agencias.application.salir_de_agencia import SalirDeAgenciaCommand, salir_de_agencia

from agencias.domain.exceptions import UltimoAgenteConRelacionesActivas
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario
from tests.agencias.application.conftest import (
    FakeRelacionRepository,
    FakeUsuarioAgenciaRepository,
)


class TestSalirDeAgenciaConMasDeUnMiembro:
    async def test_should_leave_without_approval_when_agencia_has_more_than_one_member(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_saliente_id = uuid.uuid4()
        otro_agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_saliente_id, agencia_id)
        fake_usuario_repository.seed(otro_agente_id, agencia_id)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=uuid.uuid4()
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act
        await salir_de_agencia(
            SalirDeAgenciaCommand(agencia_id=agencia_id, agente_id=agente_saliente_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert await fake_usuario_repository.obtener_agencia_id(agente_saliente_id) is None
        assert await fake_usuario_repository.obtener_agencia_id(otro_agente_id) == agencia_id


class TestSalirDeAgenciaUltimoMiembroConRelacionesActivas:
    async def test_should_raise_ultimo_agente_when_last_member_has_active_relaciones(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, agencia_id)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=uuid.uuid4()
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act / Assert
        with pytest.raises(UltimoAgenteConRelacionesActivas):
            await salir_de_agencia(
                SalirDeAgenciaCommand(agencia_id=agencia_id, agente_id=agente_id),
                relacion_repository=fake_relacion_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert await fake_usuario_repository.obtener_agencia_id(agente_id) == agencia_id


class TestSalirDeAgenciaUltimoMiembroSinRelacionesActivas:
    async def test_should_leave_when_last_member_has_no_active_relaciones(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, agencia_id)
        # A revocada relación does not block departure.
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=uuid.uuid4()
        )
        relacion.activar()
        relacion.revocar()
        fake_relacion_repository.seed(relacion)

        # Act
        await salir_de_agencia(
            SalirDeAgenciaCommand(agencia_id=agencia_id, agente_id=agente_id),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert await fake_usuario_repository.obtener_agencia_id(agente_id) is None
