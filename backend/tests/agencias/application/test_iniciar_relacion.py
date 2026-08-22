"""Unit tests for the `iniciar_relacion` use case
(`agencias/application/iniciar_relacion.py`).

Covers task 3.10 of `openspec/changes/hu-007/tasks.md`, the "Relación
agencia-propietario iniciada por el propietario" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/iniciar_relacion.py` does not exist
yet, so this test is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.4). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `IniciarRelacionCommand`: a plain dataclass with `agencia_id: UUID`,
  `propietario_id: UUID`.
- `iniciar_relacion(command, *, relacion_repository) -> RelacionAgenciaPropietario`:
  an async function that builds
  `RelacionAgenciaPropietario.crear(agencia_id=..., propietario_id=...)`
  (starts `PENDIENTE`, per the entity's own factory) and persists it via
  `relacion_repository.guardar`.
"""

import uuid

from agencias.application.iniciar_relacion import IniciarRelacionCommand, iniciar_relacion

from agencias.domain.relacion_agencia_propietario import EstadoRelacion
from tests.agencias.application.conftest import FakeRelacionRepository


class TestIniciarRelacion:
    async def test_should_create_relacion_pendiente_when_propietario_contracts_agencia(
        self, fake_relacion_repository: FakeRelacionRepository
    ) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()

        # Act
        relacion = await iniciar_relacion(
            IniciarRelacionCommand(agencia_id=agencia_id, propietario_id=propietario_id),
            relacion_repository=fake_relacion_repository,
        )

        # Assert
        assert relacion.id is not None
        assert relacion.estado == EstadoRelacion.PENDIENTE
        assert relacion.agencia_id == agencia_id
        assert relacion.propietario_id == propietario_id
        assert fake_relacion_repository.guardar_calls == [relacion]
