"""Postgres-backed adapters for the `firma-contrato` domain ports
(`firma_contrato/domain/ports.py`).

Follows the `PolizaArrendamientoRepositoryPostgres` precedent
(`seguro_arrendamiento/infrastructure/persistence/repository.py`): every
constructor takes an injected `AsyncSession` (no commit/rollback management
here — that's the caller's/unit-of-work's job), and every method maps
between the domain entities and the persistence models in both directions,
so the domain layer never depends on SQLAlchemy.

`PolizaArrendamientoRepositoryPostgres` (read-only view for
`PolizaArrendamientoPort`) lives in
`firma_contrato/infrastructure/persistence/poliza_arrendamiento_repository.py`,
not here — it reads a table owned by `seguro_arrendamiento`, kept in its
own module so this file only ever touches tables this domain owns
(`contratos`, `arrendamientos_activos`).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from firma_contrato.domain.arrendamiento_activo import (
    ArrendamientoActivo,
    EstadoArrendamientoActivo,
)
from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.infrastructure.persistence.models import ArrendamientoActivoORM, ContratoORM


class ContratoRepositoryPostgres:
    """Postgres-backed adapter for `ContratoRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, contrato: Contrato) -> Contrato:
        """Insert a new `Contrato` and return it with `id` set."""
        modelo = self._a_orm(contrato)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, contrato: Contrato) -> Contrato:
        """Persist a state change on an already-existing `Contrato`."""
        modelo = await self._session.get(ContratoORM, contrato.id)
        if modelo is None:
            raise ValueError(f"No existe ningún ContratoORM con id={contrato.id}")
        modelo.estado = contrato.estado.value
        modelo.referencia_externa = contrato.referencia_externa
        modelo.fecha = contrato.fecha
        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_referencia_externa(self, referencia_externa: str) -> Contrato | None:
        """Return the `Contrato` whose `referencia_externa` matches, or
        `None` if none does."""
        query = select(ContratoORM).where(ContratoORM.referencia_externa == referencia_externa)
        resultado = await self._session.execute(query)
        modelo = resultado.scalars().one_or_none()
        return self._a_dominio(modelo) if modelo is not None else None

    async def listar_por_usuario(self, usuario_id: UUID) -> list[Contrato]:
        """Return every `Contrato` belonging to `usuario_id` (empty list
        if it has none)."""
        query = select(ContratoORM).where(ContratoORM.usuario_id == usuario_id)
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(contrato: Contrato) -> ContratoORM:
        return ContratoORM(
            id=contrato.id,
            usuario_id=contrato.usuario_id,
            poliza_id=contrato.poliza_id,
            inmueble_id=contrato.inmueble_id,
            estado=contrato.estado.value,
            documento_referencia=contrato.documento_referencia,
            referencia_externa=contrato.referencia_externa,
            fecha=contrato.fecha,
        )

    @staticmethod
    def _a_dominio(modelo: ContratoORM) -> Contrato:
        return Contrato(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            poliza_id=modelo.poliza_id,
            inmueble_id=modelo.inmueble_id,
            estado=EstadoContrato(modelo.estado),
            documento_referencia=modelo.documento_referencia,
            referencia_externa=modelo.referencia_externa,
            fecha=modelo.fecha,
        )


class ArrendamientoActivoRepositoryPostgres:
    """Postgres-backed adapter for `ArrendamientoActivoRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, arrendamiento: ArrendamientoActivo) -> ArrendamientoActivo:
        """Insert a new `ArrendamientoActivo` and return it with `id`
        set."""
        modelo = self._a_orm(arrendamiento)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def listar_por_usuario(self, usuario_id: UUID) -> list[ArrendamientoActivo]:
        """Return every `ArrendamientoActivo` belonging to `usuario_id`
        (empty list if it has none)."""
        query = select(ArrendamientoActivoORM).where(
            ArrendamientoActivoORM.usuario_id == usuario_id
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(arrendamiento: ArrendamientoActivo) -> ArrendamientoActivoORM:
        return ArrendamientoActivoORM(
            id=arrendamiento.id,
            usuario_id=arrendamiento.usuario_id,
            poliza_id=arrendamiento.poliza_id,
            contrato_id=arrendamiento.contrato_id,
            inmueble_id=arrendamiento.inmueble_id,
            estado=arrendamiento.estado.value,
            fecha_inicio=arrendamiento.fecha_inicio,
        )

    @staticmethod
    def _a_dominio(modelo: ArrendamientoActivoORM) -> ArrendamientoActivo:
        return ArrendamientoActivo(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            poliza_id=modelo.poliza_id,
            contrato_id=modelo.contrato_id,
            inmueble_id=modelo.inmueble_id,
            estado=EstadoArrendamientoActivo(modelo.estado),
            fecha_inicio=modelo.fecha_inicio,
        )
