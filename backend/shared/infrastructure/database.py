"""SQLAlchemy async engine, session factory and declarative base.

All persistence adapters (`*/infrastructure/persistence/models.py`) import
`Base` from here so their tables register on the same metadata object, which
Alembic's `env.py` uses for autogeneration.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from shared.infrastructure.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models across every domain."""


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async session per request.

    Commits on a successful request, rolls back on any exception raised
    while handling it. Without an explicit commit here, `AsyncSession`'s
    context manager closes (and implicitly rolls back) any still-open
    transaction on exit — every real request would flush its writes far
    enough to compute a response, then silently discard them, since nothing
    else in the request path calls `commit()` (`InmuebleRepositoryPostgres`
    intentionally leaves commit/rollback to the caller/unit-of-work, per
    `docs/backend-standards.md`'s Repository pattern). Integration tests
    never caught this: they override this dependency to share one session
    per test and read back flushed-but-uncommitted rows within the same
    transaction (see `tests/inmuebles/infrastructure/test_api.py`).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
