"""Integration tests for the `firma-contrato` persistence adapters (task
5.1 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`),
against a real PostgreSQL test database (`db_session`/`seed_inquilino` from
`backend/tests/conftest.py`) — no mocks, following the precedent of
`tests/seguro_arrendamiento/infrastructure/test_repository.py`.

TDD Red phase: `firma_contrato/infrastructure/persistence/models.py` and
`repository.py` do not exist yet, so every test here is expected to fail
with `ModuleNotFoundError` until `backend-expert` implements them (task
5.2). This file fixes, by construction, the contract to satisfy:

- `ContratoRepositoryPostgres.guardar(contrato)` inserts a new row into
  `contratos` and returns the domain entity with `id` set.
- `ContratoRepositoryPostgres.actualizar(contrato)` persists a state
  change on an existing row.
- `ContratoRepositoryPostgres.obtener_por_referencia_externa(ref)` returns
  the matching `Contrato`, or `None`.
- `ContratoRepositoryPostgres.listar_por_usuario(usuario_id)` returns every
  `Contrato` for that account.
- `ArrendamientoActivoRepositoryPostgres.guardar(arrendamiento)` inserts a
  new row into `arrendamientos_activos` and returns it with `id` set.
- `ArrendamientoActivoRepositoryPostgres.listar_por_usuario(usuario_id)`
  returns every `ArrendamientoActivo` for that account.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

# Imported so `AgenciaORM`/`PolizaArrendamientoORM` register on
# `Base.metadata` before this module's tests create the schema —
# `UsuarioORM.agencia_id` declares `ForeignKey("agencia.id")` and
# `ContratoORM.poliza_id` declares
# `ForeignKey("polizas_arrendamiento.id")`, same requirement documented in
# `tests/seguro_arrendamiento/infrastructure/test_repository.py`.
from agencias.infrastructure.persistence.models import AgenciaORM  # noqa: F401
from firma_contrato.domain.arrendamiento_activo import (
    ArrendamientoActivo,
    EstadoArrendamientoActivo,
)
from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.infrastructure.persistence.repository import (
    ArrendamientoActivoRepositoryPostgres,
    ContratoRepositoryPostgres,
)
from seguro_arrendamiento.infrastructure.persistence.models import (  # noqa: F401
    PolizaArrendamientoORM,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


async def _seed_poliza_aprobada(db_session: AsyncSession, usuario_id: uuid.UUID) -> uuid.UUID:
    """Insert a real `polizas_arrendamiento` row so `ContratoORM.poliza_id`'s
    FK constraint is satisfied — `Contrato.poliza_id` is never a random
    UUID in production, it always comes from
    `PolizaArrendamientoPort.obtener_poliza_aprobada`."""
    poliza = PolizaArrendamientoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        estado="aprobada",
        fecha=datetime.now(UTC),
    )
    db_session.add(poliza)
    await db_session.flush()
    return poliza.id


class TestContratoRepositoryPostgres:
    async def test_guardar_inserts_and_returns_contrato_with_id(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ContratoRepositoryPostgres(db_session)
        poliza_id = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        contrato = Contrato.generar(
            usuario_id=seed_inquilino.id,
            poliza_id=poliza_id,
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-texto-generado",
        )
        contrato.enviar_a_firma(referencia_externa="ext-ref-1")

        # Act
        guardado = await repository.guardar(contrato)

        # Assert
        assert guardado.id is not None
        assert guardado.usuario_id == seed_inquilino.id
        assert guardado.estado == EstadoContrato.ENVIADO_A_FIRMA
        assert guardado.referencia_externa == "ext-ref-1"

    async def test_actualizar_persists_estado_change(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ContratoRepositoryPostgres(db_session)
        poliza_id = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        contrato = Contrato.generar(
            usuario_id=seed_inquilino.id,
            poliza_id=poliza_id,
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-texto-generado",
        )
        contrato.enviar_a_firma(referencia_externa="ext-ref-2")
        guardado = await repository.guardar(contrato)
        guardado.marcar_firmado()

        # Act
        actualizado = await repository.actualizar(guardado)

        # Assert
        assert actualizado.estado == EstadoContrato.FIRMADO
        encontrado = await repository.obtener_por_referencia_externa("ext-ref-2")
        assert encontrado is not None
        assert encontrado.estado == EstadoContrato.FIRMADO

    async def test_obtener_por_referencia_externa_returns_none_when_not_found(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = ContratoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.obtener_por_referencia_externa("no-existe")

        # Assert
        assert resultado is None

    async def test_listar_por_usuario_returns_every_contrato_for_that_account(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ContratoRepositoryPostgres(db_session)
        poliza_id_1 = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        primero = Contrato.generar(
            usuario_id=seed_inquilino.id,
            poliza_id=poliza_id_1,
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-1",
        )
        await repository.guardar(primero)
        poliza_id_2 = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        segundo = Contrato.generar(
            usuario_id=seed_inquilino.id,
            poliza_id=poliza_id_2,
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-2",
        )
        await repository.guardar(segundo)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert len(resultado) == 2

    async def test_listar_por_usuario_returns_empty_list_when_no_contratos(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ContratoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert resultado == []


class TestArrendamientoActivoRepositoryPostgres:
    async def test_guardar_inserts_and_returns_arrendamiento_with_id(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        contrato_repository = ContratoRepositoryPostgres(db_session)
        poliza_id = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        contrato = Contrato.generar(
            usuario_id=seed_inquilino.id,
            poliza_id=poliza_id,
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-texto-generado",
        )
        contrato.enviar_a_firma(referencia_externa="ext-ref-3")
        contrato = await contrato_repository.guardar(contrato)
        contrato.marcar_firmado()
        contrato = await contrato_repository.actualizar(contrato)

        arrendamiento_repository = ArrendamientoActivoRepositoryPostgres(db_session)
        arrendamiento = ArrendamientoActivo.crear(contrato=contrato)

        # Act
        guardado = await arrendamiento_repository.guardar(arrendamiento)

        # Assert
        assert guardado.id is not None
        assert guardado.usuario_id == seed_inquilino.id
        assert guardado.contrato_id == contrato.id
        assert guardado.estado == EstadoArrendamientoActivo.ACTIVO

    async def test_listar_por_usuario_returns_empty_list_when_no_arrendamientos(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ArrendamientoActivoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert resultado == []
