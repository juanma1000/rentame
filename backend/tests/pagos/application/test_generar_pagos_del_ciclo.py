"""Unit tests for the `generar_pagos_del_ciclo` use case
(`pagos/application/generar_pagos_del_ciclo.py`), invoked by the monthly
job (task 9).

Covers task 3.1 of `openspec/changes/pago-mensual-renta/tasks.md`, the
"Generación automática del pago pendiente por ciclo" requirement of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md`.

TDD Red phase: `pagos/application/generar_pagos_del_ciclo.py` does not
exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 3.2).
This file fixes, by construction, the contract to satisfy:

- `generar_pagos_del_ciclo(*, arrendamiento_activo, inmueble,
  pago_repository) -> list[Pago]`: an async function that, for every
  `ArrendamientoActivo` currently active, creates exactly one `Pago`
  `pendiente` (monto = `Inmueble.valor_mensual`) unless one already
  exists unresolved for that arrendamiento — idempotent across repeated
  invocations in the same ciclo.
"""

from datetime import date

from pagos.application.generar_pagos_del_ciclo import generar_pagos_del_ciclo
from pagos.domain.pago import EstadoPago
from tests.pagos.application.conftest import (
    FakeArrendamientoActivo,
    FakeInmueble,
    FakePagoRepository,
)


class TestGenerarPagosDelCicloCreaPagoPendiente:
    async def test_creates_one_pago_pendiente_per_arrendamiento_activo(
        self,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_inmueble: FakeInmueble,
        fake_pago_repository: FakePagoRepository,
    ) -> None:
        # Arrange
        arrendamiento_id = fake_arrendamiento_activo.seed()
        info = fake_arrendamiento_activo._activos[arrendamiento_id]
        fake_inmueble.seed(
            info.inmueble_id, propietario_id=info.poliza_id, valor_mensual=1_800_000.0
        )

        # Act
        creados = await generar_pagos_del_ciclo(
            arrendamiento_activo=fake_arrendamiento_activo,
            inmueble=fake_inmueble,
            pago_repository=fake_pago_repository,
        )

        # Assert
        assert len(creados) == 1
        pago = creados[0]
        assert pago.arrendamiento_activo_id == arrendamiento_id
        assert pago.monto == 1_800_000.0
        assert pago.estado == EstadoPago.PENDIENTE
        assert pago.fecha_limite >= date.today()
        assert fake_pago_repository.guardar_calls == [pago]

    async def test_creates_one_pago_per_active_arrendamiento_when_several_exist(
        self,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_inmueble: FakeInmueble,
        fake_pago_repository: FakePagoRepository,
    ) -> None:
        # Arrange
        for _ in range(3):
            arrendamiento_id = fake_arrendamiento_activo.seed()
            info = fake_arrendamiento_activo._activos[arrendamiento_id]
            fake_inmueble.seed(
                info.inmueble_id, propietario_id=info.poliza_id, valor_mensual=1_000_000.0
            )

        # Act
        creados = await generar_pagos_del_ciclo(
            arrendamiento_activo=fake_arrendamiento_activo,
            inmueble=fake_inmueble,
            pago_repository=fake_pago_repository,
        )

        # Assert
        assert len(creados) == 3


class TestGenerarPagosDelCicloEsIdempotente:
    async def test_does_not_create_second_pago_pendiente_when_one_already_unresolved(
        self,
        fake_arrendamiento_activo: FakeArrendamientoActivo,
        fake_inmueble: FakeInmueble,
        fake_pago_repository: FakePagoRepository,
    ) -> None:
        # Arrange
        arrendamiento_id = fake_arrendamiento_activo.seed()
        info = fake_arrendamiento_activo._activos[arrendamiento_id]
        fake_inmueble.seed(
            info.inmueble_id, propietario_id=info.poliza_id, valor_mensual=1_800_000.0
        )

        primera_corrida = await generar_pagos_del_ciclo(
            arrendamiento_activo=fake_arrendamiento_activo,
            inmueble=fake_inmueble,
            pago_repository=fake_pago_repository,
        )
        assert len(primera_corrida) == 1

        # Act: run the job again for the same ciclo
        segunda_corrida = await generar_pagos_del_ciclo(
            arrendamiento_activo=fake_arrendamiento_activo,
            inmueble=fake_inmueble,
            pago_repository=fake_pago_repository,
        )

        # Assert
        assert segunda_corrida == []
        assert len(fake_pago_repository.guardar_calls) == 1
        pagos = await fake_pago_repository.listar_por_arrendamiento(arrendamiento_id)
        assert len(pagos) == 1
