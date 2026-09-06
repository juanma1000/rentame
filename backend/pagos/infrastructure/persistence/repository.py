"""Postgres-backed adapter for the `pagos` domain's own port
(`pagos/domain/ports.py`'s `PagoRepositoryPort`).

Follows the `ContratoRepositoryPostgres` precedent
(`firma_contrato/infrastructure/persistence/repository.py`): the
constructor takes an injected `AsyncSession` (no commit/rollback
management here — that's the caller's/unit-of-work's job), and every
method maps between the domain entity and the persistence model in both
directions, so the domain layer never depends on SQLAlchemy.

Read-only views over `ArrendamientoActivo`/`PolizaArrendamiento`/
`Inmueble` (owned by `firma_contrato`/`seguro_arrendamiento`/`inmuebles`)
live in their own modules in this same package, not here — same rationale
as `firma_contrato.infrastructure.persistence.poliza_arrendamiento_repository`:
this file only ever touches the table this domain owns (`pagos`).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pagos.domain.pago import EstadoPago, Pago
from pagos.infrastructure.persistence.models import PagoORM


class PagoRepositoryPostgres:
    """Postgres-backed adapter for `PagoRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, pago: Pago) -> Pago:
        """Insert a new `Pago` and return it with `id` set."""
        modelo = self._a_orm(pago)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def actualizar(self, pago: Pago) -> Pago:
        """Persist a state change on an already-existing `Pago`."""
        modelo = await self._session.get(PagoORM, pago.id)
        if modelo is None:
            raise ValueError(f"No existe ningún PagoORM con id={pago.id}")
        modelo.estado = pago.estado.value
        modelo.fecha_pago = pago.fecha_pago
        modelo.referencia_externa = pago.referencia_externa
        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, pago_id: UUID) -> Pago | None:
        """Return the `Pago` with `pago_id`, or `None` if none exists."""
        modelo = await self._session.get(PagoORM, pago_id)
        return self._a_dominio(modelo) if modelo is not None else None

    async def obtener_por_referencia_externa(self, referencia_externa: str) -> Pago | None:
        """Return the `Pago` whose `referencia_externa` matches, or
        `None` if none does."""
        query = select(PagoORM).where(PagoORM.referencia_externa == referencia_externa)
        resultado = await self._session.execute(query)
        modelo = resultado.scalars().one_or_none()
        return self._a_dominio(modelo) if modelo is not None else None

    async def listar_por_arrendamiento(self, arrendamiento_activo_id: UUID) -> list[Pago]:
        """Return every `Pago` (any estado) belonging to
        `arrendamiento_activo_id` — the full historial."""
        query = select(PagoORM).where(PagoORM.arrendamiento_activo_id == arrendamiento_activo_id)
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    async def obtener_pendiente_por_arrendamiento(
        self, arrendamiento_activo_id: UUID
    ) -> Pago | None:
        """Return an unresolved (`pendiente`) `Pago` for
        `arrendamiento_activo_id`, or `None` if it has none."""
        query = select(PagoORM).where(
            PagoORM.arrendamiento_activo_id == arrendamiento_activo_id,
            PagoORM.estado == EstadoPago.PENDIENTE.value,
        )
        resultado = await self._session.execute(query)
        modelo = resultado.scalars().first()
        return self._a_dominio(modelo) if modelo is not None else None

    @staticmethod
    def _a_orm(pago: Pago) -> PagoORM:
        return PagoORM(
            id=pago.id,
            arrendamiento_activo_id=pago.arrendamiento_activo_id,
            estado=pago.estado.value,
            monto=pago.monto,
            fecha_limite=pago.fecha_limite,
            fecha_pago=pago.fecha_pago,
            referencia_externa=pago.referencia_externa,
        )

    @staticmethod
    def _a_dominio(modelo: PagoORM) -> Pago:
        return Pago(
            id=modelo.id,
            arrendamiento_activo_id=modelo.arrendamiento_activo_id,
            estado=EstadoPago(modelo.estado),
            monto=float(modelo.monto),
            fecha_limite=modelo.fecha_limite,
            fecha_pago=modelo.fecha_pago,
            referencia_externa=modelo.referencia_externa,
        )
