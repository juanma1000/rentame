"""Unit tests for the `reasignar_responsable` use case
(`agencias/application/reasignar_responsable.py`).

Covers tasks 3.17-3.18 of `openspec/changes/hu-007/tasks.md`, the "Agente
responsable reasignable" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/reasignar_responsable.py` does not
exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 4.7). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `ReasignarResponsableCommand`: a plain dataclass with `relacion_id: UUID`,
  `solicitante_id: UUID` (the acting agente; must be a member of the
  relación's agencia), `nuevo_agente_id: UUID` (must also be a member of
  that same agencia).
- `reasignar_responsable(command, *, relacion_repository, usuario_repository)
  -> RelacionAgenciaPropietario`: an async function that:
  1. Raises `RelacionNoEncontrada` when `command.relacion_id` does not
     exist.
  2. Raises `AgenteNoEsMiembroDeAgencia` when `command.nuevo_agente_id` is
     not a member of the relación's `agencia_id` (per
     `usuario_repository.obtener_agencia_id`) — without mutating the
     relación.
  3. Otherwise calls `.reasignar_responsable(nuevo_agente_id)` on the
     relación (traceability-only, does not touch `estado`) and persists it
     via `relacion_repository.actualizar`.
"""

import uuid

import pytest

from agencias.application.reasignar_responsable import (
    ReasignarResponsableCommand,
    reasignar_responsable,
)
from agencias.domain.exceptions import AgenteNoEsMiembroDeAgencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from tests.agencias.application.conftest import (
    FakeRelacionRepository,
    FakeUsuarioAgenciaRepository,
)


class TestReasignarResponsable:
    async def test_should_reassign_when_new_responsable_is_agencia_member(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        solicitante_id = uuid.uuid4()
        nuevo_agente_id = uuid.uuid4()
        fake_usuario_repository.seed(solicitante_id, agencia_id)
        fake_usuario_repository.seed(nuevo_agente_id, agencia_id)

        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act
        assert relacion.id is not None
        result = await reasignar_responsable(
            ReasignarResponsableCommand(
                relacion_id=relacion.id,
                solicitante_id=solicitante_id,
                nuevo_agente_id=nuevo_agente_id,
            ),
            relacion_repository=fake_relacion_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert result.agente_responsable_id == nuevo_agente_id
        assert result.estado == EstadoRelacion.ACTIVA
        assert relacion in fake_relacion_repository.actualizar_calls


class TestReasignarResponsableRejectsNonMemberTarget:
    async def test_should_raise_agente_no_es_miembro_when_new_responsable_is_not_a_member(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        otra_agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        solicitante_id = uuid.uuid4()
        agente_ajeno_id = uuid.uuid4()
        fake_usuario_repository.seed(solicitante_id, agencia_id)
        fake_usuario_repository.seed(agente_ajeno_id, otra_agencia_id)

        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act / Assert
        assert relacion.id is not None
        with pytest.raises(AgenteNoEsMiembroDeAgencia):
            await reasignar_responsable(
                ReasignarResponsableCommand(
                    relacion_id=relacion.id,
                    solicitante_id=solicitante_id,
                    nuevo_agente_id=agente_ajeno_id,
                ),
                relacion_repository=fake_relacion_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert relacion.agente_responsable_id is None
        assert fake_relacion_repository.actualizar_calls == []


class TestReasignarResponsableRejectsNonMemberSolicitante:
    async def test_should_raise_agente_no_es_miembro_when_solicitante_is_not_a_member(
        self,
        fake_relacion_repository: FakeRelacionRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange: the relación belongs to `agencia_id`, but `solicitante_id`
        # (the acting agente) belongs to a different agencia and tries to
        # reassign the responsable to a legitimate member of `agencia_id`.
        agencia_id = uuid.uuid4()
        otra_agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()
        solicitante_id = uuid.uuid4()
        nuevo_agente_id = uuid.uuid4()
        fake_usuario_repository.seed(solicitante_id, otra_agencia_id)
        fake_usuario_repository.seed(nuevo_agente_id, agencia_id)

        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )
        relacion.activar()
        fake_relacion_repository.seed(relacion)

        # Act / Assert
        assert relacion.id is not None
        with pytest.raises(AgenteNoEsMiembroDeAgencia):
            await reasignar_responsable(
                ReasignarResponsableCommand(
                    relacion_id=relacion.id,
                    solicitante_id=solicitante_id,
                    nuevo_agente_id=nuevo_agente_id,
                ),
                relacion_repository=fake_relacion_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert relacion.agente_responsable_id is None
        assert fake_relacion_repository.actualizar_calls == []
