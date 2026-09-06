"""Postgres-backed adapter for `PolizaArrendamientoPort`
(`pagos/domain/ports.py`).

Read-only view over `seguro_arrendamiento`'s `polizas_arrendamiento`
table — this domain only ever reads `prima_mensual`, never modifies the
póliza (proposal.md Impact: "lectura de PolizaArrendamiento.prima_mensual
... sin modificarlo").
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from seguro_arrendamiento.infrastructure.persistence.models import PolizaArrendamientoORM


class PolizaArrendamientoRepositoryPostgres:
    """Postgres-backed adapter for `PolizaArrendamientoPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_prima_mensual(self, poliza_id: UUID) -> float | None:
        """Return the `prima_mensual` of the `PolizaArrendamiento` with
        `poliza_id`, or `None` if it does not exist or has no prima
        recorded."""
        query = select(PolizaArrendamientoORM.prima_mensual).where(
            PolizaArrendamientoORM.id == poliza_id
        )
        resultado = await self._session.execute(query)
        valor = resultado.scalars().first()
        return float(valor) if valor is not None else None
