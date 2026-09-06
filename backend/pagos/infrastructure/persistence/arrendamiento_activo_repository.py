"""Postgres-backed adapter for `ArrendamientoActivoPort`
(`pagos/domain/ports.py`).

Read-only view over `firma_contrato`'s `arrendamientos_activos` table —
same rationale as
`firma_contrato.infrastructure.persistence.poliza_arrendamiento_repository.
PolizaArrendamientoRepositoryPostgres` reading `seguro_arrendamiento`'s
table: this domain never modifies `ArrendamientoActivo` (proposal.md
Impact: "lectura de ArrendamientoActivo ... sin modificarlo"), it only
reads `poliza_id`/`inmueble_id` to build each Pago's split, and the list
of currently-active arrendamientos to drive the monthly job.

Kept in its own module (not alongside `PagoRepositoryPostgres` in
`repository.py`) so that file only ever touches the table this domain
owns (`pagos`).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from firma_contrato.infrastructure.persistence.models import ArrendamientoActivoORM
from pagos.domain.ports import ArrendamientoActivoInfo


class ArrendamientoActivoRepositoryPostgres:
    """Postgres-backed adapter for `ArrendamientoActivoPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_activos(self) -> list[ArrendamientoActivoInfo]:
        """Return every `ArrendamientoActivo` — the domain's only estado
        (`activo`, per `firma_contrato.domain.arrendamiento_activo.
        EstadoArrendamientoActivo`) means every row currently qualifies."""
        query = select(ArrendamientoActivoORM)
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_info(modelo) for modelo in modelos]

    async def obtener(self, arrendamiento_activo_id: UUID) -> ArrendamientoActivoInfo | None:
        """Return the `ArrendamientoActivo` with `arrendamiento_activo_id`,
        or `None` if none exists."""
        modelo = await self._session.get(ArrendamientoActivoORM, arrendamiento_activo_id)
        return self._a_info(modelo) if modelo is not None else None

    @staticmethod
    def _a_info(modelo: ArrendamientoActivoORM) -> ArrendamientoActivoInfo:
        return ArrendamientoActivoInfo(
            id=modelo.id,
            poliza_id=modelo.poliza_id,
            inmueble_id=modelo.inmueble_id,
        )
