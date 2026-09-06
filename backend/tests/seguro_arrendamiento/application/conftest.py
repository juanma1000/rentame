"""In-memory fakes for the `seguro-arrendamiento` outbound ports
(`seguro_arrendamiento/domain/ports.py`).

Test doubles only — no production code lives here. Same pattern as
`tests/identidad/application/conftest.py`: fakes satisfy the `Protocol`s
structurally (no inheritance needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from seguro_arrendamiento.domain.poliza_arrendamiento import PolizaArrendamiento
from seguro_arrendamiento.domain.ports import ResultadoPoliza


@dataclass
class FakePolizaArrendamientoRepository:
    """In-memory stand-in for `PolizaArrendamientoRepositoryPort`."""

    _polizas: dict[UUID, PolizaArrendamiento] = field(default_factory=dict)
    guardar_calls: list[PolizaArrendamiento] = field(default_factory=list)

    async def guardar(self, poliza: PolizaArrendamiento) -> PolizaArrendamiento:
        self.guardar_calls.append(poliza)
        poliza.id = uuid4()
        self._polizas[poliza.id] = poliza
        return poliza

    async def listar_por_usuario(self, usuario_id: UUID) -> list[PolizaArrendamiento]:
        return [p for p in self._polizas.values() if p.usuario_id == usuario_id]


@dataclass
class FakeUsuarioIdentidad:
    """In-memory stand-in for `UsuarioIdentidadPort`."""

    _verificado_por_usuario: dict[UUID, bool] = field(default_factory=dict)

    def seed(self, usuario_id: UUID, verificado: bool) -> None:
        self._verificado_por_usuario[usuario_id] = verificado

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        return self._verificado_por_usuario.get(usuario_id, False)


@dataclass
class StubProveedorSeguroArrendamiento:
    """Test-only stub of `ProveedorSeguroArrendamientoPort` with a
    configurable, fixed response — used by tests covering the rejection
    path (task 3.2), which must not depend on the shared `FakeAdapter`
    (design.md: that one always approves)."""

    resultado: ResultadoPoliza
    calls: list[tuple[str, list[bytes]]] = field(default_factory=list)

    async def contratar(self, *, cedula: str, documentos: list[bytes]) -> ResultadoPoliza:
        self.calls.append((cedula, documentos))
        return self.resultado


@pytest.fixture
def fake_poliza_repository() -> FakePolizaArrendamientoRepository:
    return FakePolizaArrendamientoRepository()


@pytest.fixture
def fake_usuario_identidad() -> FakeUsuarioIdentidad:
    return FakeUsuarioIdentidad()
