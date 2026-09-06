"""Postgres-backed adapters for the `identidad` domain ports
(`identidad/domain/ports.py`).

Follows the `AgenciaRepositoryPostgres`/`UsuarioAgenciaRepositoryPostgres`
precedent (`agencias/infrastructure/persistence/repository.py`): every
constructor takes an injected `AsyncSession` (no commit/rollback management
here — that's the caller's/unit-of-work's job), and every method maps
between the domain entities and the `identidad`/`usuarios` persistence
models in both directions, so the domain layer never depends on SQLAlchemy.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identidad.domain.validacion_identidad import EstadoValidacion, ValidacionIdentidad
from identidad.infrastructure.persistence.models import ValidacionIdentidadORM
from usuarios.infrastructure.persistence.models import UsuarioORM


class ValidacionIdentidadRepositoryPostgres:
    """Postgres-backed adapter for `ValidacionIdentidadRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, validacion: ValidacionIdentidad) -> ValidacionIdentidad:
        """Insert a new `ValidacionIdentidad` and return it with `id` set."""
        modelo = self._a_orm(validacion)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def listar_por_usuario(self, usuario_id: UUID) -> list[ValidacionIdentidad]:
        """Return every `ValidacionIdentidad` attempt belonging to `usuario_id`
        (empty list if it has none)."""
        query = select(ValidacionIdentidadORM).where(
            ValidacionIdentidadORM.usuario_id == usuario_id
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(validacion: ValidacionIdentidad) -> ValidacionIdentidadORM:
        return ValidacionIdentidadORM(
            id=validacion.id,
            usuario_id=validacion.usuario_id,
            cedula=validacion.cedula,
            estado=validacion.estado.value,
            fecha=validacion.fecha,
            referencia_externa=validacion.referencia_externa,
        )

    @staticmethod
    def _a_dominio(modelo: ValidacionIdentidadORM) -> ValidacionIdentidad:
        return ValidacionIdentidad(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            cedula=modelo.cedula,
            estado=EstadoValidacion(modelo.estado),
            fecha=modelo.fecha,
            referencia_externa=modelo.referencia_externa,
        )


class UsuarioIdentidadRepositoryPostgres:
    """Postgres-backed adapter for `UsuarioIdentidadRepositoryPort`.

    Backed directly by `usuario.identidad_verificada`
    (`usuarios/infrastructure/persistence/models.py`), same rationale as
    `agencias.infrastructure.persistence.repository.
    UsuarioAgenciaRepositoryPostgres` for `usuario.agencia_id`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        """Return the current value of `usuario.identidad_verificada`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            return False
        return modelo.identidad_verificada

    async def marcar_verificado(self, usuario_id: UUID) -> None:
        """Set `usuario.identidad_verificada = True` for `usuario_id`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            raise ValueError(f"usuario {usuario_id} not found")
        modelo.identidad_verificada = True
        await self._session.flush()
