"""Unit tests for the `crear_agencia` use case
(`agencias/application/crear_agencia.py`).

Covers tasks 3.1-3.2 of `openspec/changes/hu-007/tasks.md`, the "Creación de
agencia" and "Cardinalidad de membresía agente-agencia" requirements of
`openspec/changes/hu-007/specs/agencias/spec.md`.

TDD Red phase: `agencias/application/crear_agencia.py` does not exist yet,
so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.1). This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `CrearAgenciaCommand`: a plain dataclass with `razon_social: str`,
  `nit: str`, `agente_id: UUID`.
- `crear_agencia(command, *, agencia_repository, usuario_repository) -> Agencia`:
  an async function that:
  1. Raises `AgenteYaTieneAgencia` when
     `usuario_repository.obtener_agencia_id(command.agente_id)` is not
     `None` — without calling `agencia_repository.guardar`.
  2. Otherwise builds `Agencia.crear(razon_social=..., nit=...)`, persists it
     via `agencia_repository.guardar`, and links the creating agente as its
     first member via `usuario_repository.asignar_agencia(agente_id, agencia.id)`.
"""

import uuid

import pytest

from agencias.application.crear_agencia import CrearAgenciaCommand, crear_agencia
from agencias.domain.exceptions import AgenteYaTieneAgencia
from tests.agencias.application.conftest import (
    FakeAgenciaRepository,
    FakeUsuarioAgenciaRepository,
)


class TestCrearAgencia:
    async def test_should_create_agencia_and_link_creating_agente_as_first_member(
        self,
        fake_agencia_repository: FakeAgenciaRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, None)

        # Act
        agencia = await crear_agencia(
            CrearAgenciaCommand(
                razon_social="Inmobiliaria del Valle",
                nit="900123456-1",
                agente_id=agente_id,
            ),
            agencia_repository=fake_agencia_repository,
            usuario_repository=fake_usuario_repository,
        )

        # Assert
        assert agencia.id is not None
        assert fake_agencia_repository.guardar_calls == [agencia]
        assert await fake_usuario_repository.obtener_agencia_id(agente_id) == agencia.id


class TestCrearAgenciaRejectsAgenteConAgencia:
    async def test_should_raise_agente_ya_tiene_agencia_when_agente_already_has_one(
        self,
        fake_agencia_repository: FakeAgenciaRepository,
        fake_usuario_repository: FakeUsuarioAgenciaRepository,
    ) -> None:
        # Arrange
        agente_id = uuid.uuid4()
        agencia_existente_id = uuid.uuid4()
        fake_usuario_repository.seed(agente_id, agencia_existente_id)

        # Act / Assert
        with pytest.raises(AgenteYaTieneAgencia):
            await crear_agencia(
                CrearAgenciaCommand(
                    razon_social="Otra Inmobiliaria",
                    nit="900999999-9",
                    agente_id=agente_id,
                ),
                agencia_repository=fake_agencia_repository,
                usuario_repository=fake_usuario_repository,
            )

        assert fake_agencia_repository.guardar_calls == []
        assert await fake_usuario_repository.obtener_agencia_id(agente_id) == agencia_existente_id
