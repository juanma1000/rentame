"""Integration tests for the `identidad` persistence adapters
(task 4.1 of `openspec/changes/validacion-identidad-inquilino/tasks.md`),
against a real PostgreSQL test database (`db_session`/`seed_inquilino` from
`backend/tests/conftest.py`) — no mocks, following the precedent of
`tests/agencias/infrastructure/test_repository.py`.

TDD Red phase: `identidad/infrastructure/persistence/models.py` and
`repository.py` do not exist yet, so every test here is expected to fail
with `ModuleNotFoundError` until `backend-expert` implements them (task
4.2). This file fixes, by construction, the contract to satisfy:

- `ValidacionIdentidadRepositoryPostgres.guardar(validacion)` inserts a new
  row into `validaciones_identidad` and returns the domain entity with
  `id` set — never persisting raw image bytes (they never reach this
  layer in the first place, per spec.md).
- `ValidacionIdentidadRepositoryPostgres.listar_por_usuario(usuario_id)`
  returns every `ValidacionIdentidad` for that account, empty list if none.
- `UsuarioIdentidadRepositoryPostgres.esta_verificado`/`marcar_verificado`
  read/write `usuario.identidad_verificada` directly.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Imported so `AgenciaORM` registers on `Base.metadata` before this module's
# tests create the schema — `usuario.agencia_id` declares
# `ForeignKey("agencia.id")`, and SQLAlchemy raises `NoReferencedTableError`
# on the first `create_all`/flush otherwise. Same requirement documented in
# `tests/agencias/infrastructure/test_repository.py`.
from agencias.infrastructure.persistence.models import AgenciaORM  # noqa: F401
from identidad.domain.validacion_identidad import EstadoValidacion, ValidacionIdentidad
from identidad.infrastructure.persistence.repository import (
    UsuarioIdentidadRepositoryPostgres,
    ValidacionIdentidadRepositoryPostgres,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


class TestValidacionIdentidadRepositoryPostgres:
    async def test_guardar_inserts_and_returns_validacion_with_id(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ValidacionIdentidadRepositoryPostgres(db_session)
        validacion = ValidacionIdentidad.iniciar(
            usuario_id=seed_inquilino.id, cedula="1002003004", validaciones_existentes=[]
        )
        validacion.aprobar(referencia_externa="ext-ref-1")

        # Act
        guardada = await repository.guardar(validacion)

        # Assert
        assert guardada.id is not None
        assert guardada.usuario_id == seed_inquilino.id
        assert guardada.estado == EstadoValidacion.APROBADO
        assert guardada.referencia_externa == "ext-ref-1"

    async def test_listar_por_usuario_returns_every_attempt_for_that_account(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ValidacionIdentidadRepositoryPostgres(db_session)
        primero = ValidacionIdentidad.iniciar(
            usuario_id=seed_inquilino.id, cedula="1002003004", validaciones_existentes=[]
        )
        primero.rechazar(referencia_externa="ext-ref-rechazo")
        await repository.guardar(primero)

        segundo = ValidacionIdentidad.iniciar(
            usuario_id=seed_inquilino.id,
            cedula="1002003004",
            validaciones_existentes=[],
        )
        segundo.aprobar(referencia_externa="ext-ref-aprobado")
        await repository.guardar(segundo)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert len(resultado) == 2
        estados = {v.estado for v in resultado}
        assert estados == {EstadoValidacion.RECHAZADO, EstadoValidacion.APROBADO}

    async def test_listar_por_usuario_returns_empty_list_when_no_attempts(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = ValidacionIdentidadRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert resultado == []


class TestUsuarioIdentidadRepositoryPostgres:
    async def test_esta_verificado_is_false_for_new_usuario(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = UsuarioIdentidadRepositoryPostgres(db_session)

        # Act / Assert
        assert await repository.esta_verificado(seed_inquilino.id) is False

    async def test_marcar_verificado_sets_identidad_verificada_true(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = UsuarioIdentidadRepositoryPostgres(db_session)

        # Act
        await repository.marcar_verificado(seed_inquilino.id)

        # Assert
        assert await repository.esta_verificado(seed_inquilino.id) is True
