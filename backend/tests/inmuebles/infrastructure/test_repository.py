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
