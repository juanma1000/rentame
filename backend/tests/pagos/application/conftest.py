"""In-memory fakes for the `pagos` outbound ports (`pagos/domain/ports.py`).

Test doubles only — no production code lives here. Same pattern as
`tests/firma_contrato/application/conftest.py`: fakes satisfy the
`Protocol`s structurally (no inheritance needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from pagos.domain.pago import Pago
from pagos.domain.ports import (
    ArrendamientoActivoInfo,
    InmuebleInfo,
    ResultadoCobro,
    SplitPago,
)


@dataclass
class FakePagoRepository:
    """In-memory stand-in for `PagoRepositoryPort`."""

    _pagos: dict[UUID, Pago] = field(default_factory=dict)
    guardar_calls: list[Pago] = field(default_factory=list)
    actualizar_calls: list[Pago] = field(default_factory=list)

    async def guardar(self, pago: Pago) -> Pago:
        self.guardar_calls.append(pago)
        pago.id = uuid4()
        self._pagos[pago.id] = pago
        return pago

    async def actualizar(self, pago: Pago) -> Pago:
        self.actualizar_calls.append(pago)
        assert pago.id is not None
        self._pagos[pago.id] = pago
        return pago

    async def obtener_por_id(self, pago_id: UUID) -> Pago | None:
        return self._pagos.get(pago_id)

    async def obtener_por_referencia_externa(self, referencia_externa: str) -> Pago | None:
        for pago in self._pagos.values():
            if pago.referencia_externa == referencia_externa:
                return pago
        return None

    async def listar_por_arrendamiento(self, arrendamiento_activo_id: UUID) -> list[Pago]:
        return [
            p for p in self._pagos.values() if p.arrendamiento_activo_id == arrendamiento_activo_id
        ]

    async def obtener_pendiente_por_arrendamiento(
        self, arrendamiento_activo_id: UUID
    ) -> Pago | None:
        from pagos.domain.pago import EstadoPago

        for pago in self._pagos.values():
            if (
                pago.arrendamiento_activo_id == arrendamiento_activo_id
                and pago.estado == EstadoPago.PENDIENTE
            ):
                return pago
        return None


@dataclass
class FakeArrendamientoActivo:
    """In-memory stand-in for `ArrendamientoActivoPort`."""

    _activos: dict[UUID, ArrendamientoActivoInfo] = field(default_factory=dict)

    def seed(self, *, poliza_id: UUID | None = None, inmueble_id: UUID | None = None) -> UUID:
        info = ArrendamientoActivoInfo(
            id=uuid4(),
            poliza_id=poliza_id or uuid4(),
            inmueble_id=inmueble_id or uuid4(),
        )
        self._activos[info.id] = info
        return info.id

    async def listar_activos(self) -> list[ArrendamientoActivoInfo]:
        return list(self._activos.values())

    async def obtener(self, arrendamiento_activo_id: UUID) -> ArrendamientoActivoInfo | None:
        return self._activos.get(arrendamiento_activo_id)


@dataclass
class FakePolizaArrendamiento:
    """In-memory stand-in for `PolizaArrendamientoPort`."""

    _prima_por_poliza: dict[UUID, float] = field(default_factory=dict)

    def seed_prima(self, poliza_id: UUID, prima_mensual: float) -> None:
        self._prima_por_poliza[poliza_id] = prima_mensual

    async def obtener_prima_mensual(self, poliza_id: UUID) -> float | None:
        return self._prima_por_poliza.get(poliza_id)


@dataclass
class FakeInmueble:
    """In-memory stand-in for `InmueblePort`."""

    _inmuebles: dict[UUID, InmuebleInfo] = field(default_factory=dict)

    def seed(self, inmueble_id: UUID, *, propietario_id: UUID, valor_mensual: float) -> None:
        self._inmuebles[inmueble_id] = InmuebleInfo(
            propietario_id=propietario_id, valor_mensual=valor_mensual
        )

    async def obtener(self, inmueble_id: UUID) -> InmuebleInfo | None:
        return self._inmuebles.get(inmueble_id)


@dataclass
class StubPasarelaPagos:
    """Test-only stub of `PasarelaPagosPort` with a configurable, fixed
    response."""

    resultado: ResultadoCobro
    calls: list[SplitPago] = field(default_factory=list)

    async def iniciar_cobro(self, split: SplitPago) -> ResultadoCobro:
        self.calls.append(split)
        return self.resultado


@pytest.fixture
def fake_pago_repository() -> FakePagoRepository:
    return FakePagoRepository()


@pytest.fixture
def fake_arrendamiento_activo() -> FakeArrendamientoActivo:
    return FakeArrendamientoActivo()


@pytest.fixture
def fake_poliza_arrendamiento() -> FakePolizaArrendamiento:
    return FakePolizaArrendamiento()


@pytest.fixture
def fake_inmueble() -> FakeInmueble:
    return FakeInmueble()
