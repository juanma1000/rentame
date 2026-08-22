"""Unit tests for the `buscar_agencias` use case
(`agencias/application/buscar_agencias.py`).

Covers the "Búsqueda pública de agencias" requirement of
`openspec/changes/hu-008/specs/agencias/spec.md`. This is a read-only,
pass-through use case per `openspec/changes/hu-008/design.md` decisión 4
(kept as a use case for consistency with the rest of the project, even
though the router could call the repository directly).

TDD Red phase: `agencias/application/buscar_agencias.py` does not exist yet,
so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it. This file fixes, by construction, the
contract `backend-expert` must satisfy:

- `BuscarAgenciasCommand`: a plain dataclass with `texto: str`.
- `buscar_agencias(command, *, agencia_repository) -> list[Agencia]`: an
  async function that delegates to
  `agencia_repository.buscar(command.texto)` and returns whatever it
  returns (including an empty list when there are no matches — never an
  exception for "no results").
"""

import pytest

from agencias.application.buscar_agencias import BuscarAgenciasCommand, buscar_agencias
from agencias.domain.agencia import Agencia
from tests.agencias.application.conftest import FakeAgenciaRepository


class TestBuscarAgenciasEncuentraCoincidencia:
    async def test_should_return_agencia_matching_razon_social(
        self,
        fake_agencia_repository: FakeAgenciaRepository,
    ) -> None:
        # Arrange
        agencia = fake_agencia_repository.seed(
            Agencia.crear(razon_social="Inmobiliaria del Valle S.A.S.", nit="900123456-7")
        )

        # Act
        resultado = await buscar_agencias(
            BuscarAgenciasCommand(texto="del Valle"),
            agencia_repository=fake_agencia_repository,
        )

        # Assert
        assert resultado == [agencia]

    async def test_should_return_agencia_matching_nit(
        self,
        fake_agencia_repository: FakeAgenciaRepository,
    ) -> None:
        # Arrange
        agencia = fake_agencia_repository.seed(
            Agencia.crear(razon_social="Inmobiliaria del Valle S.A.S.", nit="900123456-7")
        )

        # Act
        resultado = await buscar_agencias(
            BuscarAgenciasCommand(texto="900123456"),
            agencia_repository=fake_agencia_repository,
        )

        # Assert
        assert resultado == [agencia]


class TestBuscarAgenciasSinCoincidencias:
    async def test_should_return_empty_list_when_nothing_matches(
        self,
        fake_agencia_repository: FakeAgenciaRepository,
    ) -> None:
        # Arrange
        fake_agencia_repository.seed(
            Agencia.crear(razon_social="Inmobiliaria del Valle S.A.S.", nit="900123456-7")
        )

        # Act
        resultado = await buscar_agencias(
            BuscarAgenciasCommand(texto="texto-que-no-coincide-con-nada"),
            agencia_repository=fake_agencia_repository,
        )

        # Assert
        assert resultado == []
