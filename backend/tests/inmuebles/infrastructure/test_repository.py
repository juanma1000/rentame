"""Integration tests for `InmuebleRepositoryPostgres`
(`inmuebles/infrastructure/persistence/repository.py`).

Covers task 5.4 of `openspec/changes/hu-001/tasks.md`: these tests exercise
the real `InmuebleRepositoryPort` implementation against the actual test
database (`rentame_test`, via the `db_session` fixture of
`backend/tests/conftest.py`) instead of the in-memory fakes used by the
application-layer tests
(`backend/tests/inmuebles/application/conftest.py`).

TDD Red phase: none of the following exist yet:
- `inmuebles/infrastructure/persistence/repository.py`
  (`InmuebleRepositoryPostgres`, task 5.3)
- `inmuebles/infrastructure/persistence/models.py`
  (`InmuebleORM`, `FotoInmuebleORM`, task 5.2)
- the Alembic migration creating the `inmueble`/`foto_inmueble` tables
  (task 5.1)

Every test here is therefore expected to fail today, either with
`ModuleNotFoundError` (repository module doesn't exist) or, once that module
exists but before the migration/ORM models land, with a database error
(undefined table `inmueble`/`foto_inmueble`). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `InmuebleRepositoryPostgres(session: AsyncSession)`: constructor takes the
  injected `AsyncSession`, mirroring the `CandidateRepository` precedent in
  `docs/backend-standards.md` ("Patrón Repository") since no in-repo
  precedent exists yet for a Postgres-backed repository.
- `guardar(inmueble)`: inserts the `Inmueble` row and every `FotoInmueble` in
  `inmueble.fotos`, assigns a real UUID `id` (from `docs/architecture/
  architecture.md`'s `INMUEBLE.id`), and returns the persisted instance.
- `actualizar(inmueble)`: persists changes to an already-saved `Inmueble`
  (data edits and/or `estado`) without creating a duplicate row.
- `obtener_por_id(inmueble_id)`: returns the full `Inmueble` aggregate
  (including its `fotos`, ordered by `orden`) or `None` if it does not exist.
- `listar_por_propietario(propietario_id)`: returns only the `Inmueble`s
  owned by the given `propietario_id`.

Every test relies on `db_session`'s per-test rollback (see
`backend/tests/conftest.py`) to avoid leaking data between tests instead of
issuing explicit deletes, following the same pattern already used by
`seed_propietario`.
"""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from usuarios.infrastructure.persistence.models import UsuarioORM


def _build_foto(orden: int = 1, *, es_principal: bool = False) -> FotoInmueble:
    return FotoInmueble(
        url_storage=f"https://storage.example.com/inmuebles/fotos/{orden}.jpg",
        storage_key=f"inmuebles/fotos/{orden}.jpg",
        orden=orden,
        es_principal=es_principal,
    )


def _build_inmueble(
    propietario_id: uuid.UUID, *, fotos_count: int = 2, **overrides: object
) -> Inmueble:
    fotos = [_build_foto(orden=n, es_principal=(n == 1)) for n in range(1, fotos_count + 1)]
    kwargs: dict[str, object] = {
        "propietario_id": propietario_id,
        "direccion": "Calle 10 # 20-30",
        "barrio": "El Poblado",
        "ciudad": "Medellin",
        "tipo": "apartamento",
        "area_m2": Decimal("65.5"),
        "habitaciones": 2,
        "banos": 2,
        "valor_mensual": Decimal("1500000"),
        "descripcion": "Apartamento amoblado cerca al metro",
        "fotos": fotos,
    }
    kwargs.update(overrides)
    return Inmueble.crear(**kwargs)  # type: ignore[arg-type]


async def _seed_otro_propietario(db_session: AsyncSession) -> UsuarioORM:
    """Insert a second "propietario" user, distinct from `seed_propietario`.

    Needed by `listar_por_propietario` tests, which must prove that
    inmuebles belonging to other owners are excluded from the result.
    """
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"otro-propietario-{uuid.uuid4()}@example.com",
        rol="propietario",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


class TestInmuebleRepositoryPostgresGuardar:
    async def test_should_persist_inmueble_with_fotos_and_be_retrievable_by_id(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        inmueble = _build_inmueble(seed_propietario.id, fotos_count=2)

        # Act
        guardado = await repository.guardar(inmueble)
        await db_session.flush()
        recuperado = await repository.obtener_por_id(guardado.id)

        # Assert
        assert guardado.id is not None
        assert recuperado is not None
        assert recuperado.id == guardado.id
        assert recuperado.propietario_id == seed_propietario.id
        assert recuperado.direccion == "Calle 10 # 20-30"
        assert recuperado.barrio == "El Poblado"
        assert recuperado.ciudad == "Medellin"
        assert recuperado.tipo == "apartamento"
        assert recuperado.area_m2 == Decimal("65.5")
        assert recuperado.habitaciones == 2
        assert recuperado.banos == 2
        assert recuperado.valor_mensual == Decimal("1500000")
        assert recuperado.descripcion == "Apartamento amoblado cerca al metro"
        assert recuperado.estado == EstadoInmueble.DISPONIBLE

        fotos_ordenadas = sorted(recuperado.fotos, key=lambda foto: foto.orden)
        assert len(fotos_ordenadas) == 2
        assert fotos_ordenadas[0].orden == 1
        assert fotos_ordenadas[0].es_principal is True
        assert fotos_ordenadas[0].storage_key == "inmuebles/fotos/1.jpg"
        assert fotos_ordenadas[1].orden == 2
        assert fotos_ordenadas[1].es_principal is False


class TestInmuebleRepositoryPostgresActualizar:
    async def test_should_persist_estado_change_when_updating_existing_inmueble(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        inmueble = _build_inmueble(seed_propietario.id, fotos_count=1)
        guardado = await repository.guardar(inmueble)
        await db_session.flush()
        assert guardado.estado == EstadoInmueble.DISPONIBLE

        # Act
        guardado.despublicar()
        await repository.actualizar(guardado)
        await db_session.flush()
        recuperado = await repository.obtener_por_id(guardado.id)

        # Assert
        assert recuperado is not None
        assert recuperado.id == guardado.id
        assert recuperado.estado == EstadoInmueble.OCULTO


class TestInmuebleRepositoryPostgresListarPorPropietario:
    async def test_should_return_only_inmuebles_of_given_propietario(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        otro_propietario = await _seed_otro_propietario(db_session)

        inmueble_1 = _build_inmueble(seed_propietario.id, fotos_count=1, direccion="Calle 1 # 1-01")
        inmueble_2 = _build_inmueble(seed_propietario.id, fotos_count=1, direccion="Calle 2 # 2-02")
        inmueble_ajeno = _build_inmueble(
            otro_propietario.id, fotos_count=1, direccion="Calle 99 # 99-99"
        )

        await repository.guardar(inmueble_1)
        await repository.guardar(inmueble_2)
        await repository.guardar(inmueble_ajeno)
        await db_session.flush()

        # Act
        propios = await repository.listar_por_propietario(seed_propietario.id)

        # Assert
        assert len(propios) == 2
        assert {inmueble.direccion for inmueble in propios} == {
            "Calle 1 # 1-01",
            "Calle 2 # 2-02",
        }
        assert all(inmueble.propietario_id == seed_propietario.id for inmueble in propios)

    async def test_should_return_empty_list_when_propietario_has_no_inmuebles(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)

        # Act
        propios = await repository.listar_por_propietario(seed_propietario.id)

        # Assert
        assert propios == []


class TestInmuebleRepositoryPostgresListarPorPropietarios:
    """Covers task 5.2 of `openspec/changes/hu-002/tasks.md`: real integration
    tests, against Postgres, for `listar_por_propietarios(propietario_ids)`
    (already implemented ahead of schedule in task 5.1, per hu-002
    `design.md` decisión 6).
    """

    async def test_should_return_inmuebles_of_multiple_propietarios_excluding_unlisted(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        propietario_2 = await _seed_otro_propietario(db_session)
        propietario_3 = await _seed_otro_propietario(db_session)

        inmueble_1 = _build_inmueble(seed_propietario.id, fotos_count=1, direccion="Calle 1 # 1-01")
        inmueble_2 = _build_inmueble(propietario_2.id, fotos_count=1, direccion="Calle 2 # 2-02")
        inmueble_3 = _build_inmueble(propietario_3.id, fotos_count=1, direccion="Calle 3 # 3-03")

        await repository.guardar(inmueble_1)
        await repository.guardar(inmueble_2)
        await repository.guardar(inmueble_3)
        await db_session.flush()

        # Act
        resultado = await repository.listar_por_propietarios(
            [seed_propietario.id, propietario_3.id]
        )

        # Assert: propietario_2 (id2) is omitted from the query, so its
        # inmueble must not appear in the result.
        assert len(resultado) == 2
        assert {inmueble.direccion for inmueble in resultado} == {
            "Calle 1 # 1-01",
            "Calle 3 # 3-03",
        }
        assert {inmueble.propietario_id for inmueble in resultado} == {
            seed_propietario.id,
            propietario_3.id,
        }

    async def test_should_return_empty_list_when_propietario_ids_is_empty(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        await repository.guardar(_build_inmueble(seed_propietario.id, fotos_count=1))
        await db_session.flush()

        # Act
        resultado = await repository.listar_por_propietarios([])

        # Assert
        assert resultado == []


class TestInmuebleRepositoryPostgresListarDisponibles:
    """Covers `openspec/changes/hu-003/specs/inmuebles/spec.md` requirement
    "Listado público de inmuebles disponibles" and `design.md` decisión 2 of
    that change: real integration tests, against Postgres, for the new
    `listar_disponibles()` method.

    TDD Red phase: `listar_disponibles` does not exist yet on
    `InmuebleRepositoryPostgres`, so every test here is expected to fail with
    `AttributeError` until `backend-expert` adds it. This class fixes, by
    construction, the contract `backend-expert` must satisfy:

    - `listar_disponibles() -> list[Inmueble]`: returns every `Inmueble`
      whose `estado` is `EstadoInmueble.DISPONIBLE` (filters at the query
      level, `WHERE estado = 'disponible'`), regardless of owner, and an
      empty list when none match.
    """

    async def test_should_return_only_inmuebles_in_estado_disponible(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        otro_propietario = await _seed_otro_propietario(db_session)

        disponible_1 = _build_inmueble(
            seed_propietario.id, fotos_count=1, direccion="Calle 1 # 1-01"
        )
        disponible_2 = _build_inmueble(
            otro_propietario.id, fotos_count=1, direccion="Calle 2 # 2-02"
        )
        oculto = _build_inmueble(seed_propietario.id, fotos_count=1, direccion="Calle 3 # 3-03")
        no_disponible = _build_inmueble(
            otro_propietario.id, fotos_count=1, direccion="Calle 4 # 4-04"
        )

        guardado_disponible_1 = await repository.guardar(disponible_1)
        guardado_disponible_2 = await repository.guardar(disponible_2)
        guardado_oculto = await repository.guardar(oculto)
        guardado_no_disponible = await repository.guardar(no_disponible)
        await db_session.flush()

        guardado_oculto.despublicar()
        await repository.actualizar(guardado_oculto)
        guardado_no_disponible.marcar_no_disponible()
        await repository.actualizar(guardado_no_disponible)
        await db_session.flush()

        # Act
        disponibles = await repository.listar_disponibles()

        # Assert
        assert {inmueble.id for inmueble in disponibles} == {
            guardado_disponible_1.id,
            guardado_disponible_2.id,
        }
        assert all(inmueble.estado == EstadoInmueble.DISPONIBLE for inmueble in disponibles)

    async def test_should_return_empty_list_when_no_inmueble_is_disponible(
        self, db_session: AsyncSession, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        repository = InmuebleRepositoryPostgres(db_session)
        oculto = _build_inmueble(seed_propietario.id, fotos_count=1)
        guardado_oculto = await repository.guardar(oculto)
        await db_session.flush()

        guardado_oculto.despublicar()
        await repository.actualizar(guardado_oculto)
        await db_session.flush()

        # Act
        disponibles = await repository.listar_disponibles()

        # Assert
        assert disponibles == []
