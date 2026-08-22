"""Shared pytest fixtures.

`db_session` / `seed_propietario` connect to `settings.test_database_url`
(a separate database from dev, see `docker/postgres/init-test-db.sh`) and are
meant for the integration tests of later phases (repository, endpoints).
They are not exercised by the auth unit tests in this bootstrap phase, which
need no database at all.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.infrastructure.database import Base
from shared.infrastructure.settings import get_settings
from usuarios.infrastructure.persistence.models import UsuarioORM


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession bound to the test database, rolling back after
    each test so tests never leak state into one another.
    """
    settings = get_settings()
    engine = create_async_engine(settings.test_database_url, future=True)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def seed_propietario(db_session: AsyncSession) -> UsuarioORM:
    """Insert a test "propietario" user into the test database and return it.

    Used by future integration tests of the `inmuebles` domain, which need a
    real `usuario` row for `propietario_id` to reference via FK.
    """
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"propietario-{uuid.uuid4()}@example.com",
        rol="propietario",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


@pytest_asyncio.fixture
async def seed_agente(db_session: AsyncSession) -> UsuarioORM:
    """Insert a test "agente" user into the test database and return it.

    Used by the integration tests of the `agencias` domain (task 5.4 of
    `openspec/changes/hu-007/tasks.md`), which need a real `usuario` row with
    `rol="agente"` for `usuario.agencia_id` (task 5.2) and for
    `UsuarioAgenciaRepositoryPort` (`agencias/domain/ports.py`) to reference.
    """
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"agente-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario
