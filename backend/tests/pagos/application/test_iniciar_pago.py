"""Unit tests for the `iniciar_pago` use case
(`pagos/application/iniciar_pago.py`).

Covers task 4.1 of `openspec/changes/pago-mensual-renta/tasks.md`, the
"El inquilino inicia el pago (modelo pull)" and "Split de pago ejecutado
por la pasarela" requirements of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md`.

TDD Red phase: `pagos/application/iniciar_pago.py` does not exist yet, so
every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 4.2). This file fixes, by
construction, the contract to satisfy:

- `iniciar_pago(pago_id, *, pago_repository, arrendamiento_activo,
  poliza_arrendamiento, inmueble, pasarela) -> Pago`: an async function
  that:
  1. Raises `PagoNoEncontrado` when `pago_id` does not match any `Pago`.
  2. Raises `PagoYaCompletado` when the located `Pago` is already
     `completado` — without ever calling `pasarela.iniciar_cobro`.
  3. Otherwise assembles the split (monto total = `Pago.monto`,
     `monto_prima_retenida` = `PolizaArrendamiento.prima_mensual`,
     `propietario_id` = `Inmueble.propietario_id`) from the `Pago`'s
     `ArrendamientoActivo`, calls `pasarela.iniciar_cobro`, and marks the
     `Pago` `completado` when the pasarela resolves synchronously
     (`resultado.estado == "completado"`) or just records the
     `referencia_externa` otherwise (async pasarela, resolved later by
     the webhook).
"""

import uuid
from datetime import date, timedelta

import pytest

from pagos.application.iniciar_pago import iniciar_pago
from pagos.domain.exceptions import PagoNoEncontrado, PagoYaCompletado
from pagos.domain.pago import EstadoPago, Pago
from pagos.domain.ports import ResultadoCobro
from pagos.infrastructure.adapters.fake_adapter import FakeAdapter
from tests.pagos.application.conftest import (
    FakeArrendamientoActivo,
    FakeInmueble,
    FakePagoRepository,
    FakePolizaArrendamiento,
    StubPasarelaPagos,
)


async def _seed_pago_pendiente(
    fake_pago_repository: FakePagoRepository,
    fake_arrendamiento_activo: FakeArrendamientoActivo,
    fake_poliza_arrendamiento: FakePolizaArrendamiento,
    fake_inmueble: FakeInmueble,
    *,
    monto: float = 1_800_000.0,
    prima_mensual: float = 50_000.0,
) -> Pago:
    propietario_id = uuid.uuid4()
    arrendamiento_id = fake_arrendamiento_activo.seed()
    info = fake_arrendamiento_activo._activos[arrendamiento_id]
    fake_poliza_arrendamiento.seed_prima(info.poliza_id, prima_mensual)
    fake_inmueble.seed(info.inmueble_id, propietario_id=propietario_id, valor_mensual=monto)
    pago = Pago.crear(
        arrendamiento_activo_id=arrendamiento_id,
        monto=monto,
        fecha_limite=date.today() + timedelta(days=5),
    )
    return await fake_pago_repository.guardar(pago)


class TestIniciarPagoPagoInexistente:
    async def test_raises_pago_no_encontrado(
        self,
        fake_pago_repository: FakePagoRepository,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
        fake_inmueble: FakeInmueble,
    ) -> None:
        # Act / Assert
        with pytest.raises(PagoNoEncontrado):
            await iniciar_pago(
                uuid.uuid4(),
                pago_repository=fake_pago_repository,
                arrendamiento_activo=fake_arrendamiento_activo,
                poliza_arrendamiento=fake_poliza_arrendamiento,
                inmueble=fake_inmueble,
                pasarela=FakeAdapter(),
            )


class TestIniciarPagoYaCompletado:
    async def test_raises_without_calling_pasarela(
        self,
        fake_pago_repository: FakePagoRepository,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
        fake_inmueble: FakeInmueble,
    ) -> None:
        # Arrange
        pago = await _seed_pago_pendiente(
            fake_pago_repository,
            fake_arrendamiento_activo,
            fake_poliza_arrendamiento,
            fake_inmueble,
        )
        pago.marcar_completado(referencia_externa="ext-ya-completado")
        await fake_pago_repository.actualizar(pago)
        stub_pasarela = StubPasarelaPagos(
            resultado=ResultadoCobro(referencia_externa="no-deberia-llamarse", estado="completado")
        )

        # Act / Assert
        with pytest.raises(PagoYaCompletado):
            await iniciar_pago(
                pago.id,
                pago_repository=fake_pago_repository,
                arrendamiento_activo=fake_arrendamiento_activo,
                poliza_arrendamiento=fake_poliza_arrendamiento,
                inmueble=fake_inmueble,
                pasarela=stub_pasarela,
            )

        assert stub_pasarela.calls == []


class TestIniciarPagoPendiente:
    async def test_assembles_split_and_marks_completado_on_synchronous_result(
        self,
        fake_pago_repository: FakePagoRepository,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
        fake_inmueble: FakeInmueble,
    ) -> None:
        # Arrange
        pago = await _seed_pago_pendiente(
            fake_pago_repository,
            fake_arrendamiento_activo,
            fake_poliza_arrendamiento,
            fake_inmueble,
            monto=1_800_000.0,
            prima_mensual=50_000.0,
        )

        # Act
        actualizado = await iniciar_pago(
            pago.id,
            pago_repository=fake_pago_repository,
            arrendamiento_activo=fake_arrendamiento_activo,
            poliza_arrendamiento=fake_poliza_arrendamiento,
            inmueble=fake_inmueble,
            pasarela=FakeAdapter(),
        )

        # Assert
        assert actualizado.estado == EstadoPago.COMPLETADO
        assert actualizado.referencia_externa
        assert actualizado.fecha_pago is not None
        assert fake_pago_repository.actualizar_calls == [actualizado]

    async def test_splits_prima_retenida_and_propietario_from_arrendamiento_chain(
        self,
        fake_pago_repository: FakePagoRepository,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
        fake_inmueble: FakeInmueble,
    ) -> None:
        # Arrange
        propietario_id = uuid.uuid4()
        arrendamiento_id = fake_arrendamiento_activo.seed()
        info = fake_arrendamiento_activo._activos[arrendamiento_id]
        fake_poliza_arrendamiento.seed_prima(info.poliza_id, 75_000.0)
        fake_inmueble.seed(
            info.inmueble_id, propietario_id=propietario_id, valor_mensual=2_000_000.0
        )
        pago = await fake_pago_repository.guardar(
            Pago.crear(
                arrendamiento_activo_id=arrendamiento_id,
                monto=2_000_000.0,
                fecha_limite=date.today() + timedelta(days=5),
            )
        )
        stub_pasarela = StubPasarelaPagos(
            resultado=ResultadoCobro(referencia_externa="ext-async", estado="pendiente")
        )

        # Act
        actualizado = await iniciar_pago(
            pago.id,
            pago_repository=fake_pago_repository,
            arrendamiento_activo=fake_arrendamiento_activo,
            poliza_arrendamiento=fake_poliza_arrendamiento,
            inmueble=fake_inmueble,
            pasarela=stub_pasarela,
        )

        # Assert
        assert len(stub_pasarela.calls) == 1
        split = stub_pasarela.calls[0]
        assert split.monto_total == 2_000_000.0
        assert split.monto_prima_retenida == 75_000.0
        assert split.propietario_id == propietario_id
        # async pasarela: estado stays pendiente, referencia_externa recorded
        assert actualizado.estado == EstadoPago.PENDIENTE
        assert actualizado.referencia_externa == "ext-async"
        assert actualizado.fecha_pago is None
