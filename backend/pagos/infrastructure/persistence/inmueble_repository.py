"""Postgres-backed adapter for `InmueblePort` (`pagos/domain/ports.py`).

Read-only view over `inmuebles`' `inmueble` table — this domain only ever
reads `propietario_id`/`valor_mensual`, never modifies the inmueble
(proposal.md Impact: "lectura de ... Inmueble.propietario_id ... sin
modificarlo").
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from inmuebles.infrastructure.persistence.models import InmuebleORM
from pagos.domain.ports import InmuebleInfo


class InmuebleRepositoryPostgres:
    """Postgres-backed adapter for `InmueblePort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener(self, inmueble_id: UUID) -> InmuebleInfo | None:
        """Return the `InmuebleInfo` for `inmueble_id`, or `None` if it
        does not exist."""
        modelo = await self._session.get(InmuebleORM, inmueble_id)
        if modelo is None:
            return None
        return InmuebleInfo(
            propietario_id=modelo.propietario_id,
            valor_mensual=float(modelo.valor_mensual),
        )
