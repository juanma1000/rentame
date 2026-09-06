"""In-memory fakes for the `identidad` outbound ports
(`identidad/domain/ports.py`).

Test doubles only — no production code lives here. Same pattern as
`tests/agencias/application/conftest.py`: fakes satisfy the `Protocol`s
structurally (no inheritance needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from identidad.domain.ports import ResultadoValidacion
from identidad.domain.validacion_identidad import ValidacionIdentidad


@dataclass
class FakeValidacionIdentidadRepository:
    """In-memory stand-in for `ValidacionIdentidadRepositoryPort`."""

    _validaciones: dict[UUID, ValidacionIdentidad] = field(default_factory=dict)
    guardar_calls: list[ValidacionIdentidad] = field(default_factory=list)

    async def guardar(self, validacion: ValidacionIdentidad) -> ValidacionIdentidad:
        self.guardar_calls.append(validacion)
        validacion.id = uuid4()
        self._validaciones[validacion.id] = validacion
        return validacion

    async def listar_por_usuario(self, usuario_id: UUID) -> list[ValidacionIdentidad]:
        return [v for v in self._validaciones.values() if v.usuario_id == usuario_id]


@dataclass
class FakeUsuarioIdentidadRepository:
    """In-memory stand-in for `UsuarioIdentidadRepositoryPort`."""

    _verificado_por_usuario: dict[UUID, bool] = field(default_factory=dict)
    marcar_verificado_calls: list[UUID] = field(default_factory=list)

    def seed(self, usuario_id: UUID, verificado: bool) -> None:
        self._verificado_por_usuario[usuario_id] = verificado

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        return self._verificado_por_usuario.get(usuario_id, False)

    async def marcar_verificado(self, usuario_id: UUID) -> None:
        self.marcar_verificado_calls.append(usuario_id)
        self._verificado_por_usuario[usuario_id] = True


@dataclass
class StubProveedorValidacionIdentidad:
    """Test-only stub of `ProveedorValidacionIdentidadPort` with a
    configurable, fixed response — used by tests covering the rejection
    path (task 3.2), which must not depend on the shared `FakeAdapter`
    (design.md decisión 4: that one always approves)."""

    resultado: ResultadoValidacion
    calls: list[tuple[str, bytes, bytes]] = field(default_factory=list)

    async def validar(
        self, *, cedula: str, imagen_frente: bytes, imagen_dorso: bytes
    ) -> ResultadoValidacion:
        self.calls.append((cedula, imagen_frente, imagen_dorso))
        return self.resultado


@pytest.fixture
def fake_validacion_repository() -> FakeValidacionIdentidadRepository:
    return FakeValidacionIdentidadRepository()


@pytest.fixture
def fake_usuario_repository() -> FakeUsuarioIdentidadRepository:
    return FakeUsuarioIdentidadRepository()
