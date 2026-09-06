"""Integration tests for the `pagos` persistence adapters (task 6.1 of
`openspec/changes/pago-mensual-renta/tasks.md`), against a real PostgreSQL
test database (`db_session`/`seed_inquilino` from `backend/tests/conftest.py`)
— no mocks, following the precedent of
`tests/firma_contrato/infrastructure/test_repository.py`.

TDD Red phase: `pagos/infrastructure/persistence/models.py` and
`repository.py` do not exist yet, so every test here is expected to fail
with `ModuleNotFoundError` until `backend-expert` implements them (task
6.2). This file fixes, by construction, the contract to satisfy:

- `PagoRepositoryPostgres.guardar(pago)` inserts a new row into `pagos`
  and returns the domain entity with `id` set.
- `PagoRepositoryPostgres.actualizar(pago)` persists a state change on an
  existing row.
- `PagoRepositoryPostgres.obtener_por_id(pago_id)` returns the matching
  `Pago`, or `None`.
- `PagoRepositoryPostgres.obtener_por_referencia_externa(ref)` returns the
  matching `Pago`, or `None`.
- `PagoRepositoryPostgres.listar_por_arrendamiento(arrendamiento_activo_id)`
  returns every `Pago` for that arrendamiento (any estado — the full
  historial).
- `PagoRepositoryPostgres.obtener_pendiente_por_arrendamiento(
  arrendamiento_activo_id)` returns the unresolved (`pendiente`) `Pago`
  for that arrendamiento, or `None`.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

# Imported so `PolizaArrendamientoORM`/`ContratoORM`/`ArrendamientoActivoORM`
# register on `Base.metadata` before this module's tests create the schema —
# `PagoORM.arrendamiento_activo_id` declares
# `ForeignKey("arrendamientos_activos.id")`, same requirement documented in
# `tests/firma_contrato/infrastructure/test_repository.py`.
from agencias.infrastructure.persistence.models import AgenciaORM  # noqa: F401
from firma_contrato.infrastructure.persistence.models import (  # noqa: F401
    ArrendamientoActivoORM,
    ContratoORM,
)
from pagos.domain.pago import EstadoPago, Pago
from pagos.infrastructure.persistence.repository import PagoRepositoryPostgres
from seguro_arrendamiento.infrastructure.persistence.models import (  # noqa: F401
    PolizaArrendamientoORM,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


async def _seed_arrendamiento_activo(db_session: AsyncSession, usuario_id: uuid.UUID) -> uuid.UUID:
    """Insert a real `polizas_arrendamiento` + `contratos` +
    `arrendamientos_activos` chain so `PagoORM.arrendamiento_activo_id`'s
    FK constraint is satisfied."""
    poliza = PolizaArrendamientoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        estado="aprobada",
        fecha=datetime.now(UTC),
    )
    db_session.add(poliza)
    await db_session.flush()

    contrato = ContratoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        poliza_id=poliza.id,
        inmueble_id=uuid.uuid4(),
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
        inmueble_id=contrato.inmueble_id,
        estado="activo",
        fecha_inicio=date.today(),
    )
    db_session.add(arrendamiento)
    await db_session.flush()
    return arrendamiento.id


class TestPagoRepositoryPostgresGuardar:
    async def test_guardar_inserts_and_returns_pago_with_id(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago = Pago.crear(
            arrendamiento_activo_id=arrendamiento_id,
            monto=1_800_000.0,
            fecha_limite=date.today() + timedelta(days=5),
        )

        # Act
        guardado = await repository.guardar(pago)

        # Assert
        assert guardado.id is not None
        assert guardado.arrendamiento_activo_id == arrendamiento_id
        assert guardado.estado == EstadoPago.PENDIENTE
        assert float(guardado.monto) == 1_800_000.0


class TestPagoRepositoryPostgresActualizar:
    async def test_actualizar_persists_estado_and_fecha_pago(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago = Pago.crear(
            arrendamiento_activo_id=arrendamiento_id,
            monto=1_800_000.0,
            fecha_limite=date.today() + timedelta(days=5),
        )
        guardado = await repository.guardar(pago)
        guardado.marcar_completado(referencia_externa="ext-ref-1")

        # Act
        actualizado = await repository.actualizar(guardado)

        # Assert
        assert actualizado.estado == EstadoPago.COMPLETADO
        assert actualizado.fecha_pago is not None
        encontrado = await repository.obtener_por_referencia_externa("ext-ref-1")
        assert encontrado is not None
        assert encontrado.estado == EstadoPago.COMPLETADO


class TestPagoRepositoryPostgresObtenerPorId:
    async def test_returns_none_when_not_found(self, db_session: AsyncSession) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.obtener_por_id(uuid.uuid4())

        # Assert
        assert resultado is None


class TestPagoRepositoryPostgresObtenerPorReferenciaExterna:
    async def test_returns_none_when_not_found(self, db_session: AsyncSession) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.obtener_por_referencia_externa("no-existe")

        # Assert
        assert resultado is None


class TestPagoRepositoryPostgresListarPorArrendamiento:
    async def test_returns_every_pago_regardless_of_estado(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)

        completado = Pago.crear(
            arrendamiento_activo_id=arrendamiento_id,
            monto=1_000_000.0,
            fecha_limite=date.today() - timedelta(days=25),
        )
        completado.marcar_completado(referencia_externa="ext-completado")
        await repository.guardar(completado)

        pendiente = Pago.crear(
            arrendamiento_activo_id=arrendamiento_id,
            monto=1_000_000.0,
            fecha_limite=date.today() + timedelta(days=5),
        )
        await repository.guardar(pendiente)

        # Act
        resultado = await repository.listar_por_arrendamiento(arrendamiento_id)

        # Assert
        assert len(resultado) == 2
        estados = {p.estado for p in resultado}
        assert estados == {EstadoPago.COMPLETADO, EstadoPago.PENDIENTE}

    async def test_returns_empty_list_when_no_pagos(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)

        # Act
        resultado = await repository.listar_por_arrendamiento(arrendamiento_id)

        # Assert
        assert resultado == []


class TestPagoRepositoryPostgresObtenerPendientePorArrendamiento:
    async def test_returns_the_pending_pago(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pendiente = await repository.guardar(
            Pago.crear(
                arrendamiento_activo_id=arrendamiento_id,
                monto=1_000_000.0,
                fecha_limite=date.today() + timedelta(days=5),
            )
        )

        # Act
        resultado = await repository.obtener_pendiente_por_arrendamiento(arrendamiento_id)

        # Assert
        assert resultado is not None
        assert resultado.id == pendiente.id

    async def test_returns_none_when_only_completado_exists(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PagoRepositoryPostgres(db_session)
        arrendamiento_id = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        completado = Pago.crear(
            arrendamiento_activo_id=arrendamiento_id,
            monto=1_000_000.0,
            fecha_limite=date.today() - timedelta(days=25),
        )
        completado.marcar_completado(referencia_externa="ext-completado-2")
        await repository.guardar(completado)

        # Act
        resultado = await repository.obtener_pendiente_por_arrendamiento(arrendamiento_id)

        # Assert
        assert resultado is None
