"""In-memory fakes for the `firma-contrato` outbound ports
(`firma_contrato/domain/ports.py`).

Test doubles only — no production code lives here. Same pattern as
`tests/seguro_arrendamiento/application/conftest.py`: fakes satisfy the
`Protocol`s structurally (no inheritance needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from firma_contrato.domain.arrendamiento_activo import ArrendamientoActivo
from firma_contrato.domain.contrato import Contrato
from firma_contrato.domain.ports import ResultadoEnvioFirma


@dataclass
class FakeContratoRepository:
    """In-memory stand-in for `ContratoRepositoryPort`."""

    _contratos: dict[UUID, Contrato] = field(default_factory=dict)
    guardar_calls: list[Contrato] = field(default_factory=list)
    actualizar_calls: list[Contrato] = field(default_factory=list)

    async def guardar(self, contrato: Contrato) -> Contrato:
        self.guardar_calls.append(contrato)
        contrato.id = uuid4()
        self._contratos[contrato.id] = contrato
        return contrato

    async def actualizar(self, contrato: Contrato) -> Contrato:
        self.actualizar_calls.append(contrato)
        assert contrato.id is not None
        self._contratos[contrato.id] = contrato
        return contrato

    async def obtener_por_referencia_externa(self, referencia_externa: str) -> Contrato | None:
        for contrato in self._contratos.values():
            if contrato.referencia_externa == referencia_externa:
                return contrato
        return None

    async def listar_por_usuario(self, usuario_id: UUID) -> list[Contrato]:
        return [c for c in self._contratos.values() if c.usuario_id == usuario_id]


@dataclass
class FakeArrendamientoActivoRepository:
    """In-memory stand-in for `ArrendamientoActivoRepositoryPort`."""

    _arrendamientos: dict[UUID, ArrendamientoActivo] = field(default_factory=dict)
    guardar_calls: list[ArrendamientoActivo] = field(default_factory=list)

    async def guardar(self, arrendamiento: ArrendamientoActivo) -> ArrendamientoActivo:
        self.guardar_calls.append(arrendamiento)
        arrendamiento.id = uuid4()
        self._arrendamientos[arrendamiento.id] = arrendamiento
        return arrendamiento

    async def listar_por_usuario(self, usuario_id: UUID) -> list[ArrendamientoActivo]:
        return [a for a in self._arrendamientos.values() if a.usuario_id == usuario_id]


@dataclass
class FakePolizaArrendamiento:
    """In-memory stand-in for `PolizaArrendamientoPort`."""

    _poliza_aprobada_por_usuario: dict[UUID, UUID] = field(default_factory=dict)

    def seed_aprobada(self, usuario_id: UUID, poliza_id: UUID) -> None:
        self._poliza_aprobada_por_usuario[usuario_id] = poliza_id

    async def obtener_poliza_aprobada(self, usuario_id: UUID) -> UUID | None:
        return self._poliza_aprobada_por_usuario.get(usuario_id)


@dataclass
class StubProveedorFirmaElectronica:
    """Test-only stub of `ProveedorFirmaElectronicaPort` with a
    configurable, fixed response."""

    resultado: ResultadoEnvioFirma
    calls: list[str] = field(default_factory=list)

    async def enviar_a_firma(self, *, documento: str) -> ResultadoEnvioFirma:
        self.calls.append(documento)
        return self.resultado


@pytest.fixture
def fake_contrato_repository() -> FakeContratoRepository:
    return FakeContratoRepository()


@pytest.fixture
def fake_arrendamiento_repository() -> FakeArrendamientoActivoRepository:
    return FakeArrendamientoActivoRepository()


@pytest.fixture
def fake_poliza_arrendamiento() -> FakePolizaArrendamiento:
    return FakePolizaArrendamiento()
