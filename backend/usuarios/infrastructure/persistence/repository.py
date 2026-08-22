"""Postgres-backed adapter for the `usuarios` domain port
(`usuarios/domain/ports.py`).

Follows the `AgenciaRepositoryPostgres` precedent
(`agencias/infrastructure/persistence/repository.py`): the constructor takes
an injected `AsyncSession` (no commit/rollback management here — that's the
caller's/unit-of-work's job), and every method maps between the domain
entity and the `usuario` persistence model in both directions, so the domain
layer never depends on SQLAlchemy. `IntegrityError` raised by the database
(e.g. the `usuario.email` unique constraint) is never caught here — it
propagates to the caller, same as every other repository in this codebase.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from usuarios.domain.usuario import Usuario
from usuarios.infrastructure.persistence.models import UsuarioORM


class UsuarioRepositoryPostgres:
    """Postgres-backed adapter for `UsuarioRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, usuario: Usuario) -> Usuario:
        """Insert a new `Usuario` and return it with `id` set."""
        modelo = self._a_orm(usuario)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_email(self, email: str) -> Usuario | None:
        """Return the `Usuario` matching `email`, or `None` if it does not exist."""
        query = select(UsuarioORM).where(UsuarioORM.email == email)
        resultado = await self._session.execute(query)
        modelo = resultado.scalars().first()
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Return the `Usuario` matching `usuario_id`, or `None` if it does not exist."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    @staticmethod
    def _a_orm(usuario: Usuario) -> UsuarioORM:
        return UsuarioORM(
            id=usuario.id,
            email=usuario.email,
            password_hash=usuario.password_hash,
            nombre=usuario.nombre,
            rol=usuario.rol,
            agencia_id=usuario.agencia_id,
        )

    @staticmethod
    def _a_dominio(modelo: UsuarioORM) -> Usuario:
        return Usuario(
            id=modelo.id,
            email=modelo.email,
            password_hash=modelo.password_hash or "",
            nombre=modelo.nombre or "",
            rol=modelo.rol,
            agencia_id=modelo.agencia_id,
        )
