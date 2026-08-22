"""Integration tests for the `agencias` Postgres-backed repositories
(`agencias/infrastructure/persistence/repository.py`).

Covers task 5.4 of `openspec/changes/hu-007/tasks.md`: these tests exercise
the real adapters for `AgenciaRepositoryPort`, `RelacionRepositoryPort`,
`SolicitudIngresoRepositoryPort` and `UsuarioAgenciaRepositoryPort`
(`agencias/domain/ports.py`) against the actual test database (via the
`db_session` fixture of `backend/tests/conftest.py`), following the same
precedent as `tests/inmuebles/infrastructure/test_repository.py`.

TDD Red phase: none of the following exist yet:
- `agencias/infrastructure/persistence/repository.py`
  (`AgenciaRepositoryPostgres`, `RelacionRepositoryPostgres`,
  `SolicitudIngresoRepositoryPostgres`, `UsuarioAgenciaRepositoryPostgres`,
  task 5.3)
- `agencias/infrastructure/persistence/models.py`
  (`AgenciaORM`, `SolicitudIngresoAgenciaORM`,
  `RelacionAgenciaPropietarioORM`, task 5.2)
- the `usuario.agencia_id` column on `UsuarioORM`
  (`usuarios/infrastructure/persistence/models.py`, task 5.2)
- the Alembic migration creating the `agencia`, `solicitud_ingreso_agencia`,
  `relacion_agencia_propietario` tables and the `usuario.agencia_id` column
  (task 5.1)

Every test here is therefore expected to fail today, either with
`ModuleNotFoundError` (repository module doesn't exist), `AttributeError`
(`UsuarioORM` has no `agencia_id` yet) or, once those exist but before the
migration lands, with a database error (undefined table/column). This file
fixes, by construction, the contract `backend-expert` must satisfy:

- `AgenciaRepositoryPostgres(session: AsyncSession)`, mirroring the
  `InmuebleRepositoryPostgres` constructor precedent (injected `AsyncSession`,
  no commit/rollback management here — that's the caller's/unit-of-work's job):
  - `guardar(agencia)`: inserts the row, assigns a real UUID `id`, returns
    the persisted instance.
  - `obtener_por_id(agencia_id)`: returns the full `Agencia` or `None`.
  - `actualizar(agencia)` exists per the port but is not exercised here since
    `Agencia` currently exposes no post-creation mutation (task 2.1);
    `backend-expert` should still implement it per the port's contract.

- `SolicitudIngresoRepositoryPostgres(session: AsyncSession)`:
  - `guardar(solicitud)`: inserts the row in `estado="pendiente"`.
  - `actualizar(solicitud)`: persists an `estado` change (e.g. after calling
    `solicitud.aprobar()`) without creating a duplicate row.
  - `obtener_por_id(solicitud_id)`: returns the full `SolicitudIngreso` or
    `None`.

- `RelacionRepositoryPostgres(session: AsyncSession)`:
  - `guardar(relacion)`: inserts the row in `estado="pendiente"`,
    `agente_responsable_id=None`.
  - `actualizar(relacion)`: persists `estado` and/or
    `agente_responsable_id` changes (after `activar()`, `revocar()` or
    `reasignar_responsable()`) without creating a duplicate row.
  - `obtener_por_id(relacion_id)`: returns the full
    `RelacionAgenciaPropietario` or `None`.
  - `obtener_activa_por_propietario(propietario_id)`: returns the `ACTIVA`
    relación for that propietario, or `None` if it has none (must ignore
    `PENDIENTE`/`REVOCADA` relaciones of the same propietario).
  - `listar_por_agencia(agencia_id)`: returns every relación of that
    agencia regardless of `estado` (empty list if none).

- `UsuarioAgenciaRepositoryPostgres(session: AsyncSession)`, backed by
  `usuario.agencia_id` (design.md decisión 2 — no separate join table):
  - `asignar_agencia(usuario_id, agencia_id)`: sets the column.
  - `obtener_agencia_id(usuario_id)`: reads it back (`None` if unset).
  - `remover_agencia(usuario_id)`: sets it back to `NULL`.
  - `listar_ids_por_agencia(agencia_id)`: returns the `usuario.id` of every
    agente whose `agencia_id` equals the given value (empty list if none).

Every test relies on `db_session`'s per-test rollback (see
`backend/tests/conftest.py`) to avoid leaking data between tests instead of
issuing explicit deletes, following the same pattern already used by
`seed_propietario`/`seed_agente`.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso, SolicitudIngreso
from agencias.infrastructure.persistence.repository import (
    AgenciaRepositoryPostgres,
    RelacionRepositoryPostgres,
    SolicitudIngresoRepositoryPostgres,
    UsuarioAgenciaRepositoryPostgres,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


async def _seed_agencia(db_session: AsyncSession, **overrides: object) -> Agencia:
    """Insert a persisted `Agencia`, used as FK target by other aggregates."""
    kwargs: dict[str, object] = {
        "razon_social": "Inmobiliaria Ejemplo S.A.S.",
        "nit": f"900{uuid.uuid4().int % 1_000_000:06d}-1",
    }
    kwargs.update(overrides)
    agencia = Agencia.crear(**kwargs)  # type: ignore[arg-type]
    repository = AgenciaRepositoryPostgres(db_session)
    guardada = await repository.guardar(agencia)
    await db_session.flush()
    return guardada


async def _seed_otro_agente(db_session: AsyncSession) -> UsuarioORM:
    """Insert a second "agente" user, distinct from `seed_agente`.

    Needed by tests that must prove reasignación/listado only touches the
    intended agente.
    """
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"otro-agente-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


class TestAgenciaRepositoryPostgres:
    async def test_should_persist_agencia_and_be_retrievable_by_id(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = AgenciaRepositoryPostgres(db_session)
        agencia = Agencia.crear(razon_social="Inmobiliaria del Valle", nit="900123456-1")

        # Act
        guardada = await repository.guardar(agencia)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert guardada.id is not None
        assert recuperada is not None
        assert recuperada.id == guardada.id
        assert recuperada.razon_social == "Inmobiliaria del Valle"
        assert recuperada.nit == "900123456-1"

    async def test_should_return_none_when_agencia_does_not_exist(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = AgenciaRepositoryPostgres(db_session)

        # Act
        recuperada = await repository.obtener_por_id(uuid.uuid4())

        # Assert
        assert recuperada is None


class TestSolicitudIngresoRepositoryPostgres:
    async def test_should_persist_solicitud_pendiente_and_be_retrievable_by_id(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = SolicitudIngresoRepositoryPostgres(db_session)
        solicitud = SolicitudIngreso.crear(agencia_id=agencia.id, agente_id=seed_agente.id)

        # Act
        guardada = await repository.guardar(solicitud)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert guardada.id is not None
        assert recuperada is not None
        assert recuperada.agencia_id == agencia.id
        assert recuperada.agente_id == seed_agente.id
        assert recuperada.estado == EstadoSolicitudIngreso.PENDIENTE

    async def test_should_persist_estado_change_after_aprobar(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = SolicitudIngresoRepositoryPostgres(db_session)
        solicitud = SolicitudIngreso.crear(agencia_id=agencia.id, agente_id=seed_agente.id)
        guardada = await repository.guardar(solicitud)
        await db_session.flush()

        # Act
        guardada.aprobar()
        await repository.actualizar(guardada)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert recuperada is not None
        assert recuperada.estado == EstadoSolicitudIngreso.APROBADA


class TestRelacionRepositoryPostgres:
    async def test_should_persist_relacion_pendiente_and_be_retrievable_by_id(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = RelacionRepositoryPostgres(db_session)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia.id, propietario_id=seed_propietario.id
        )

        # Act
        guardada = await repository.guardar(relacion)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert guardada.id is not None
        assert recuperada is not None
        assert recuperada.agencia_id == agencia.id
        assert recuperada.propietario_id == seed_propietario.id
        assert recuperada.estado == EstadoRelacion.PENDIENTE
        assert recuperada.agente_responsable_id is None

    async def test_should_persist_activar_transition(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = RelacionRepositoryPostgres(db_session)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia.id, propietario_id=seed_propietario.id
        )
        guardada = await repository.guardar(relacion)
        await db_session.flush()

        # Act
        guardada.activar()
        await repository.actualizar(guardada)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert recuperada is not None
        assert recuperada.estado == EstadoRelacion.ACTIVA

    async def test_should_persist_revocar_transition(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = RelacionRepositoryPostgres(db_session)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia.id, propietario_id=seed_propietario.id
        )
        guardada = await repository.guardar(relacion)
        await db_session.flush()
        guardada.activar()
        await repository.actualizar(guardada)
        await db_session.flush()

        # Act
        guardada.revocar()
        await repository.actualizar(guardada)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert recuperada is not None
        assert recuperada.estado == EstadoRelacion.REVOCADA

    async def test_should_persist_reasignar_responsable_without_changing_estado(
        self,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
        seed_agente: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        otro_agente = await _seed_otro_agente(db_session)
        repository = RelacionRepositoryPostgres(db_session)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia.id, propietario_id=seed_propietario.id
        )
        guardada = await repository.guardar(relacion)
        await db_session.flush()
        guardada.activar()
        await repository.actualizar(guardada)
        await db_session.flush()

        # Act
        guardada.reasignar_responsable(otro_agente.id)
        await repository.actualizar(guardada)
        await db_session.flush()
        recuperada = await repository.obtener_por_id(guardada.id)

        # Assert
        assert recuperada is not None
        assert recuperada.agente_responsable_id == otro_agente.id
        assert recuperada.estado == EstadoRelacion.ACTIVA

    async def test_obtener_activa_por_propietario_should_return_only_the_active_one(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        agencia_revocada = await _seed_agencia(db_session, nit="900111111-1")
        agencia_activa = await _seed_agencia(db_session, nit="900222222-1")
        repository = RelacionRepositoryPostgres(db_session)

        relacion_revocada = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_revocada.id, propietario_id=seed_propietario.id
        )
        guardada_revocada = await repository.guardar(relacion_revocada)
        await db_session.flush()
        guardada_revocada.activar()
        guardada_revocada.revocar()
        await repository.actualizar(guardada_revocada)
        await db_session.flush()

        relacion_activa = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_activa.id, propietario_id=seed_propietario.id
        )
        guardada_activa = await repository.guardar(relacion_activa)
        await db_session.flush()
        guardada_activa.activar()
        await repository.actualizar(guardada_activa)
        await db_session.flush()

        # Act
        resultado = await repository.obtener_activa_por_propietario(seed_propietario.id)

        # Assert
        assert resultado is not None
        assert resultado.id == guardada_activa.id
        assert resultado.estado == EstadoRelacion.ACTIVA

    async def test_obtener_activa_por_propietario_should_return_none_when_no_active_relacion(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = RelacionRepositoryPostgres(db_session)

        # Act
        resultado = await repository.obtener_activa_por_propietario(seed_propietario.id)

        # Assert
        assert resultado is None

    async def test_listar_por_agencia_should_return_every_relacion_of_that_agencia(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        otra_agencia = await _seed_agencia(db_session, nit="900333333-1")
        otro_propietario = UsuarioORM(
            id=uuid.uuid4(),
            email=f"otro-propietario-{uuid.uuid4()}@example.com",
            rol="propietario",
        )
        db_session.add(otro_propietario)
        await db_session.flush()

        repository = RelacionRepositoryPostgres(db_session)
        relacion_1 = await repository.guardar(
            RelacionAgenciaPropietario.crear(
                agencia_id=agencia.id, propietario_id=seed_propietario.id
            )
        )
        relacion_2 = await repository.guardar(
            RelacionAgenciaPropietario.crear(
                agencia_id=agencia.id, propietario_id=otro_propietario.id
            )
        )
        await repository.guardar(
            RelacionAgenciaPropietario.crear(
                agencia_id=otra_agencia.id, propietario_id=seed_propietario.id
            )
        )
        await db_session.flush()

        # Act
        resultado = await repository.listar_por_agencia(agencia.id)

        # Assert
        assert {relacion.id for relacion in resultado} == {relacion_1.id, relacion_2.id}
        assert all(relacion.agencia_id == agencia.id for relacion in resultado)

    async def test_listar_por_agencia_should_return_empty_list_when_agencia_has_no_relaciones(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = RelacionRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_por_agencia(agencia.id)

        # Assert
        assert resultado == []


class TestUsuarioAgenciaRepositoryPostgres:
    async def test_asignar_agencia_should_be_readable_via_obtener_agencia_id(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = UsuarioAgenciaRepositoryPostgres(db_session)

        # Act
        await repository.asignar_agencia(seed_agente.id, agencia.id)
        await db_session.flush()
        resultado = await repository.obtener_agencia_id(seed_agente.id)

        # Assert
        assert resultado == agencia.id

    async def test_obtener_agencia_id_should_return_none_when_agente_has_no_agencia(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        repository = UsuarioAgenciaRepositoryPostgres(db_session)

        # Act
        resultado = await repository.obtener_agencia_id(seed_agente.id)

        # Assert
        assert resultado is None

    async def test_remover_agencia_should_clear_the_pointer(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = UsuarioAgenciaRepositoryPostgres(db_session)
        await repository.asignar_agencia(seed_agente.id, agencia.id)
        await db_session.flush()

        # Act
        await repository.remover_agencia(seed_agente.id)
        await db_session.flush()
        resultado = await repository.obtener_agencia_id(seed_agente.id)

        # Assert
        assert resultado is None

    async def test_listar_ids_por_agencia_should_return_only_members_of_that_agencia(
        self, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        otra_agencia = await _seed_agencia(db_session, nit="900444444-1")
        otro_agente = await _seed_otro_agente(db_session)
        agente_de_otra_agencia = await _seed_otro_agente(db_session)

        repository = UsuarioAgenciaRepositoryPostgres(db_session)
        await repository.asignar_agencia(seed_agente.id, agencia.id)
        await repository.asignar_agencia(otro_agente.id, agencia.id)
        await repository.asignar_agencia(agente_de_otra_agencia.id, otra_agencia.id)
        await db_session.flush()

        # Act
        resultado = await repository.listar_ids_por_agencia(agencia.id)

        # Assert
        assert set(resultado) == {seed_agente.id, otro_agente.id}

    async def test_listar_ids_por_agencia_should_return_empty_list_when_no_members(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        repository = UsuarioAgenciaRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_ids_por_agencia(agencia.id)

        # Assert
        assert resultado == []
