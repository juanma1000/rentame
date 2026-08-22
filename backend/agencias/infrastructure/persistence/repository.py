"""Postgres-backed adapters for the `agencias` domain ports
(`agencias/domain/ports.py`).

Follows the `InmuebleRepositoryPostgres` precedent
(`inmuebles/infrastructure/persistence/repository.py`): every constructor
takes an injected `AsyncSession` (no commit/rollback management here — that's
the caller's/unit-of-work's job, per `docs/backend-standards.md`'s Repository
pattern and `design.md` decisión 3), and every method maps between the
domain entities and the `agencias`/`usuarios` persistence models in both
directions, so the domain layer never depends on SQLAlchemy.
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso, SolicitudIngreso
from agencias.infrastructure.persistence.models import (
    AgenciaORM,
    RelacionAgenciaPropietarioORM,
    SolicitudIngresoAgenciaORM,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


class AgenciaRepositoryPostgres:
    """Postgres-backed adapter for `AgenciaRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, agencia: Agencia) -> Agencia:
        """Insert a new `Agencia` and return it with `id` set."""
        modelo = self._a_orm(agencia)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, agencia: Agencia) -> Agencia:
        """Persist changes to an existing `Agencia`."""
        if agencia.id is None:
            raise ValueError("cannot actualizar an Agencia without an id")

        modelo = await self._session.get(AgenciaORM, agencia.id)
        if modelo is None:
            raise ValueError(f"Agencia {agencia.id} not found")

        modelo.razon_social = agencia.razon_social
        modelo.nit = agencia.nit

        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, agencia_id: UUID) -> Agencia | None:
        """Return the `Agencia` matching `agencia_id`, or `None` if it does not exist."""
        modelo = await self._session.get(AgenciaORM, agencia_id)
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    async def buscar(self, texto: str) -> list[Agencia]:
        """Return every `Agencia` whose `razon_social`/`nit` matches `texto`
        (case-insensitive substring, `ILIKE '%<texto>%'`), per `design.md`
        decisión 4. Empty list when there is no match."""
        patron = f"%{texto}%"
        query = select(AgenciaORM).where(
            or_(AgenciaORM.razon_social.ilike(patron), AgenciaORM.nit.ilike(patron))
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(agencia: Agencia) -> AgenciaORM:
        return AgenciaORM(
            id=agencia.id,
            razon_social=agencia.razon_social,
            nit=agencia.nit,
        )

    @staticmethod
    def _a_dominio(modelo: AgenciaORM) -> Agencia:
        return Agencia(
            id=modelo.id,
            razon_social=modelo.razon_social,
            nit=modelo.nit,
        )


class SolicitudIngresoRepositoryPostgres:
    """Postgres-backed adapter for `SolicitudIngresoRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        """Insert a new `SolicitudIngreso` and return it with `id` set."""
        modelo = self._a_orm(solicitud)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, solicitud: SolicitudIngreso) -> SolicitudIngreso:
        """Persist changes to an existing `SolicitudIngreso`."""
        if solicitud.id is None:
            raise ValueError("cannot actualizar a SolicitudIngreso without an id")

        modelo = await self._session.get(SolicitudIngresoAgenciaORM, solicitud.id)
        if modelo is None:
            raise ValueError(f"SolicitudIngreso {solicitud.id} not found")

        modelo.estado = solicitud.estado.value

        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, solicitud_id: UUID) -> SolicitudIngreso | None:
        """Return the solicitud matching `solicitud_id`, or `None` if it does not exist."""
        modelo = await self._session.get(SolicitudIngresoAgenciaORM, solicitud_id)
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    @staticmethod
    def _a_orm(solicitud: SolicitudIngreso) -> SolicitudIngresoAgenciaORM:
        return SolicitudIngresoAgenciaORM(
            id=solicitud.id,
            agencia_id=solicitud.agencia_id,
            agente_id=solicitud.agente_id,
            estado=solicitud.estado.value,
        )

    @staticmethod
    def _a_dominio(modelo: SolicitudIngresoAgenciaORM) -> SolicitudIngreso:
        return SolicitudIngreso(
            id=modelo.id,
            agencia_id=modelo.agencia_id,
            agente_id=modelo.agente_id,
            estado=EstadoSolicitudIngreso(modelo.estado),
        )


class RelacionRepositoryPostgres:
    """Postgres-backed adapter for `RelacionRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        """Insert a new `RelacionAgenciaPropietario` and return it with `id` set."""
        modelo = self._a_orm(relacion)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietario:
        """Persist changes to an existing `RelacionAgenciaPropietario`."""
        if relacion.id is None:
            raise ValueError("cannot actualizar a RelacionAgenciaPropietario without an id")

        modelo = await self._session.get(RelacionAgenciaPropietarioORM, relacion.id)
        if modelo is None:
            raise ValueError(f"RelacionAgenciaPropietario {relacion.id} not found")

        modelo.estado = relacion.estado.value
        modelo.agente_responsable_id = relacion.agente_responsable_id

        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, relacion_id: UUID) -> RelacionAgenciaPropietario | None:
        """Return the relación matching `relacion_id`, or `None` if it does not exist."""
        modelo = await self._session.get(RelacionAgenciaPropietarioORM, relacion_id)
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    async def obtener_activa_por_propietario(
        self, propietario_id: UUID
    ) -> RelacionAgenciaPropietario | None:
        """Return the `ACTIVA` relación for `propietario_id`, or `None` if it has none."""
        query = select(RelacionAgenciaPropietarioORM).where(
            RelacionAgenciaPropietarioORM.propietario_id == propietario_id,
            RelacionAgenciaPropietarioORM.estado == EstadoRelacion.ACTIVA.value,
        )
        resultado = await self._session.execute(query)
        modelo = resultado.scalars().first()
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    async def listar_por_agencia(self, agencia_id: UUID) -> list[RelacionAgenciaPropietario]:
        """Return every relación belonging to `agencia_id` (empty list if none)."""
        query = select(RelacionAgenciaPropietarioORM).where(
            RelacionAgenciaPropietarioORM.agencia_id == agencia_id
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(relacion: RelacionAgenciaPropietario) -> RelacionAgenciaPropietarioORM:
        return RelacionAgenciaPropietarioORM(
            id=relacion.id,
            agencia_id=relacion.agencia_id,
            propietario_id=relacion.propietario_id,
            estado=relacion.estado.value,
            agente_responsable_id=relacion.agente_responsable_id,
        )

    @staticmethod
    def _a_dominio(modelo: RelacionAgenciaPropietarioORM) -> RelacionAgenciaPropietario:
        return RelacionAgenciaPropietario(
            id=modelo.id,
            agencia_id=modelo.agencia_id,
            propietario_id=modelo.propietario_id,
            estado=EstadoRelacion(modelo.estado),
            agente_responsable_id=modelo.agente_responsable_id,
        )


class UsuarioAgenciaRepositoryPostgres:
    """Postgres-backed adapter for `UsuarioAgenciaRepositoryPort`.

    Per `design.md` decisión 2, backed directly by `usuario.agencia_id`
    (`usuarios/infrastructure/persistence/models.py`) rather than a separate
    join table.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_agencia_id(self, usuario_id: UUID) -> UUID | None:
        """Return the `agencia_id` currently assigned to `usuario_id`, or `None`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            return None
        return modelo.agencia_id

    async def asignar_agencia(self, usuario_id: UUID, agencia_id: UUID) -> None:
        """Set `usuario.agencia_id = agencia_id` for `usuario_id`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            raise ValueError(f"usuario {usuario_id} not found")
        modelo.agencia_id = agencia_id
        await self._session.flush()

    async def remover_agencia(self, usuario_id: UUID) -> None:
        """Set `usuario.agencia_id = NULL` for `usuario_id`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            raise ValueError(f"usuario {usuario_id} not found")
        modelo.agencia_id = None
        await self._session.flush()

    async def listar_ids_por_agencia(self, agencia_id: UUID) -> list[UUID]:
        """Return the `usuario.id` of every agente whose `agencia_id` equals `agencia_id`."""
        query = select(UsuarioORM.id).where(UsuarioORM.agencia_id == agencia_id)
        resultado = await self._session.execute(query)
        return list(resultado.scalars().all())
