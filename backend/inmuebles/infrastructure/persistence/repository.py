"""`InmuebleRepositoryPort` implementation backed by PostgreSQL.

Follows the `CandidateRepository` pattern in `docs/backend-standards.md`
("Patrón Repository"): the constructor takes an injected `AsyncSession`
(no session management here — the caller/unit-of-work owns commit/rollback),
and every method maps between the `Inmueble`/`FotoInmueble` domain entities
and the `InmuebleORM`/`FotoInmuebleORM` persistence models (task 5.2) in both
directions, so the domain layer never depends on SQLAlchemy.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.infrastructure.persistence.models import FotoInmuebleORM, InmuebleORM


class InmuebleRepositoryPostgres:
    """Postgres-backed adapter for `InmuebleRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, inmueble: Inmueble) -> Inmueble:
        """Insert a new `Inmueble` (and its `fotos`) and return it with `id` set."""
        modelo = self._a_orm(inmueble)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, inmueble: Inmueble) -> Inmueble:
        """Persist changes to an existing `Inmueble` (data edits and/or `estado`)."""
        if inmueble.id is None:
            raise ValueError("cannot actualizar an Inmueble without an id")

        modelo = await self._session.get(
            InmuebleORM, inmueble.id, options=[selectinload(InmuebleORM.fotos)]
        )
        if modelo is None:
            raise ValueError(f"Inmueble {inmueble.id} not found")

        modelo.direccion = inmueble.direccion
        modelo.barrio = inmueble.barrio
        modelo.ciudad = inmueble.ciudad
        modelo.tipo = inmueble.tipo
        modelo.area_m2 = inmueble.area_m2
        modelo.habitaciones = inmueble.habitaciones
        modelo.banos = inmueble.banos
        modelo.valor_mensual = inmueble.valor_mensual
        modelo.descripcion = inmueble.descripcion
        modelo.estado = inmueble.estado.value

        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, inmueble_id: UUID) -> Inmueble | None:
        """Return the full `Inmueble` aggregate (with its `fotos`, ordered by
        `orden`) or `None` if it does not exist.
        """
        modelo = await self._session.get(
            InmuebleORM, inmueble_id, options=[selectinload(InmuebleORM.fotos)]
        )
        if modelo is None:
            return None
        return self._a_dominio(modelo)

    async def listar_por_propietario(self, propietario_id: UUID) -> list[Inmueble]:
        """Return every `Inmueble` owned by `propietario_id` (empty list if none)."""
        query = (
            select(InmuebleORM)
            .where(InmuebleORM.propietario_id == propietario_id)
            .options(selectinload(InmuebleORM.fotos))
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(inmueble: Inmueble) -> InmuebleORM:
        """Map a domain `Inmueble` (plus its `fotos`) to a new `InmuebleORM`."""
        return InmuebleORM(
            id=inmueble.id,
            propietario_id=inmueble.propietario_id,
            agente_id=inmueble.agente_id,
            direccion=inmueble.direccion,
            barrio=inmueble.barrio,
            ciudad=inmueble.ciudad,
            tipo=inmueble.tipo,
            area_m2=inmueble.area_m2,
            habitaciones=inmueble.habitaciones,
            banos=inmueble.banos,
            valor_mensual=inmueble.valor_mensual,
            descripcion=inmueble.descripcion,
            estado=inmueble.estado.value,
            fotos=[
                FotoInmuebleORM(
                    url_storage=foto.url_storage,
                    storage_key=foto.storage_key,
                    orden=foto.orden,
                    es_principal=foto.es_principal,
                )
                for foto in inmueble.fotos
            ],
        )

    @staticmethod
    def _a_dominio(modelo: InmuebleORM) -> Inmueble:
        """Map an `InmuebleORM` (plus its `fotos`) back to a domain `Inmueble`."""
        fotos = sorted(modelo.fotos, key=lambda foto: foto.orden)
        return Inmueble(
            id=modelo.id,
            propietario_id=modelo.propietario_id,
            agente_id=modelo.agente_id,
            direccion=modelo.direccion,
            barrio=modelo.barrio,
            ciudad=modelo.ciudad,
            tipo=modelo.tipo,
            area_m2=modelo.area_m2,
            habitaciones=modelo.habitaciones,
            banos=modelo.banos,
            valor_mensual=modelo.valor_mensual,
            descripcion=modelo.descripcion,
            fotos=[
                FotoInmueble(
                    url_storage=foto.url_storage,
                    storage_key=foto.storage_key,
                    orden=foto.orden,
                    es_principal=foto.es_principal,
                )
                for foto in fotos
            ],
            estado=EstadoInmueble(modelo.estado),
        )
