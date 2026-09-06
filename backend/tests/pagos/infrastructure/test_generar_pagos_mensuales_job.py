"""Integration test for the monthly `pagos` job's entrypoint
(`scripts/generar_pagos_mensuales.py`), task 9.2 of
`openspec/changes/pago-mensual-renta/tasks.md`.

Confirms the entrypoint's wiring (`generar_pagos_mensuales`) runs against
a real PostgreSQL test database (`db_session`/`seed_inquilino` from
`backend/tests/conftest.py`) — no mocks — and that running it twice for
the same ciclo does not duplicate `Pago`s (design.md decisión 4: this is
the actual mechanism that makes a possibly-retried ECS task invocation
safe, not just the use case's own unit tests).
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from agencias.infrastructure.persistence.models import AgenciaORM  # noqa: F401
from firma_contrato.infrastructure.persistence.models import ArrendamientoActivoORM, ContratoORM
from inmuebles.infrastructure.persistence.models import InmuebleORM
from pagos.infrastructure.persistence.repository import PagoRepositoryPostgres
from scripts.generar_pagos_mensuales import generar_pagos_mensuales
from seguro_arrendamiento.infrastructure.persistence.models import PolizaArrendamientoORM
from usuarios.infrastructure.persistence.models import UsuarioORM


async def _seed_arrendamiento_activo(db_session: AsyncSession, usuario_id: uuid.UUID) -> uuid.UUID:
    propietario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"propietario-{uuid.uuid4()}@example.com",
        rol="propietario",
    )
    db_session.add(propietario)
    await db_session.flush()

    inmueble = InmuebleORM(
        id=uuid.uuid4(),
        propietario_id=propietario.id,
        direccion="Calle 10 # 20-30",
        barrio="Centro",
        ciudad="Cali",
        tipo="apartamento",
        area_m2=Decimal("60.0"),
        habitaciones=2,
        banos=1,
        valor_mensual=Decimal("1800000"),
        descripcion="Apartamento de prueba",
        estado="no_disponible",
    )
    db_session.add(inmueble)
    await db_session.flush()

    poliza = PolizaArrendamientoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        estado="aprobada",
        fecha=datetime.now(UTC),
        prima_mensual=Decimal("50000.00"),
    )
    db_session.add(poliza)
    await db_session.flush()

    contrato = ContratoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        poliza_id=poliza.id,
        inmueble_id=inmueble.id,
        estado="firmado",
        documento_referencia="contrato-texto-generado",
        fecha=datetime.now(UTC),
    )
    db_session.add(contrato)
    await db_session.flush()

    arrendamiento = ArrendamientoActivoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        poliza_id=poliza.id,
        contrato_id=contrato.id,
        inmueble_id=inmueble.id,
        estado="activo",
        fecha_inicio=date.today(),
    )
    db_session.add(arrendamiento)
    await db_session.flush()

    return arrendamiento.id


class TestGenerarPagosMensualesJob:
    async def test_creates_pago_pendiente_against_real_database(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)

        # Act
        creados = await generar_pagos_mensuales(db_session)

        # Assert
        assert len(creados) == 1
        assert creados[0].arrendamiento_activo_id == arrendamiento_id
        assert creados[0].monto == 1_800_000.0

        pago_repository = PagoRepositoryPostgres(db_session)
        pagos = await pago_repository.listar_por_arrendamiento(arrendamiento_id)
        assert len(pagos) == 1

    async def test_is_idempotent_when_run_twice_in_the_same_ciclo(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)

        # Act
        primera_corrida = await generar_pagos_mensuales(db_session)
        segunda_corrida = await generar_pagos_mensuales(db_session)

        # Assert
        assert len(primera_corrida) == 1
        assert segunda_corrida == []

        pago_repository = PagoRepositoryPostgres(db_session)
        pagos = await pago_repository.listar_por_arrendamiento(arrendamiento_id)
        assert len(pagos) == 1
