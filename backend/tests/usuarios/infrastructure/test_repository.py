"""Integration tests for the `usuarios` Postgres-backed repository
(`usuarios/infrastructure/persistence/repository.py`), covering task 3.2 of
`openspec/changes/hu-008/tasks.md`.

These tests exercise the real adapter for `UsuarioRepositoryPort`
(`usuarios/domain/ports.py`) against the actual test database (via the
`db_session` fixture of `backend/tests/conftest.py`), following the same
precedent as `tests/agencias/infrastructure/test_repository.py`.

TDD Red phase: `usuarios/infrastructure/persistence/repository.py` does not
exist yet (task 3.3). Every test below is therefore expected to fail with
`ModuleNotFoundError`/`ImportError` today. This file fixes, by construction,
the contract `backend-expert` must satisfy:

- `UsuarioRepositoryPostgres(session: AsyncSession)`, mirroring the
  `AgenciaRepositoryPostgres` constructor precedent (injected `AsyncSession`,
  no commit/rollback management here — that's the caller's/unit-of-work's
  job):
  - `guardar(usuario)`: inserts the row, assigns a real UUID `id`, returns
    the persisted instance (including `password_hash`/`nombre`/`rol`).
  - `obtener_por_email(email)`: returns the full `Usuario` or `None` when no
    row matches.
  - `obtener_por_id(usuario_id)`: returns the full `Usuario` or `None` when
    no row matches.

- Uniqueness of `usuario.email`: the `usuario.email` column already has a
  `unique=True` constraint (`usuarios/infrastructure/persistence/models.py`).
  Inserting two `Usuario`s with the same email through `guardar` twice (i.e.
  bypassing the use-case-level `obtener_por_email` pre-check that
  `registrar_usuario` performs) must fail at the database level. This test
  asserts the repository does NOT silently swallow that failure — it lets
  the database's `IntegrityError` (via SQLAlchemy) propagate to the caller,
  same as every other repository in this codebase (none of them catch
  `IntegrityError`). `backend-expert` should not add any duplicate-check
  logic inside `UsuarioRepositoryPostgres.guardar` — the use-case layer
  (`registrar_usuario`, already Green) is the one responsible for raising
  the domain-level `EmailYaRegistrado` before ever calling `guardar`; this
  test only documents/pins the lower-level DB behavior as a safety net.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from usuarios.domain.usuario import Usuario
from usuarios.infrastructure.persistence.repository import UsuarioRepositoryPostgres


def _build_usuario(**overrides: object) -> Usuario:
    kwargs: dict[str, object] = {
        "email": f"usuario-{uuid.uuid4()}@example.com",
        "password": "contrasena-segura-123",
        "nombre": "Ana Perez",
        "rol": "propietario",
    }
    kwargs.update(overrides)
    return Usuario.crear(**kwargs)  # type: ignore[arg-type]


class TestUsuarioRepositoryPostgresGuardarYObtener:
    async def test_should_persist_usuario_and_be_retrievable_by_email(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = UsuarioRepositoryPostgres(db_session)
        email = f"propietario-{uuid.uuid4()}@example.com"
        usuario = _build_usuario(email=email, nombre="Carlos Ruiz", rol="propietario")

        # Act
        guardado = await repository.guardar(usuario)
        await db_session.flush()
        recuperado = await repository.obtener_por_email(email)

        # Assert
        assert guardado.id is not None
        assert recuperado is not None
        assert recuperado.id == guardado.id
        assert recuperado.email == email
        assert recuperado.nombre == "Carlos Ruiz"
        assert recuperado.rol == "propietario"
        assert recuperado.password_hash == usuario.password_hash

    async def test_should_return_none_when_email_does_not_exist(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = UsuarioRepositoryPostgres(db_session)

        # Act
        recuperado = await repository.obtener_por_email(f"inexistente-{uuid.uuid4()}@example.com")

        # Assert
        assert recuperado is None

    async def test_should_persist_usuario_and_be_retrievable_by_id(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = UsuarioRepositoryPostgres(db_session)
        usuario = _build_usuario(rol="agente")

        # Act
        guardado = await repository.guardar(usuario)
        await db_session.flush()
        recuperado = await repository.obtener_por_id(guardado.id)

        # Assert
        assert recuperado is not None
        assert recuperado.id == guardado.id
        assert recuperado.email == usuario.email
        assert recuperado.rol == "agente"

    async def test_should_return_none_when_id_does_not_exist(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = UsuarioRepositoryPostgres(db_session)

        # Act
        recuperado = await repository.obtener_por_id(uuid.uuid4())

        # Assert
        assert recuperado is None


class TestUsuarioRepositoryPostgresUnicidadDeEmail:
    async def test_should_raise_integrity_error_when_inserting_duplicate_email(
        self, db_session: AsyncSession
    ) -> None:
        # Arrange
        repository = UsuarioRepositoryPostgres(db_session)
        email = f"duplicado-{uuid.uuid4()}@example.com"
        primero = _build_usuario(email=email)
        segundo = _build_usuario(email=email)
        await repository.guardar(primero)
        await db_session.flush()

        # Act / Assert: the DB-level unique constraint on usuario.email must
        # reject the second insert with the same email — the repository must
        # not swallow this error.
        with pytest.raises(IntegrityError):
            await repository.guardar(segundo)
            await db_session.flush()
