"""Postgres-backed adapter for `PolizaArrendamientoPort`
(`firma_contrato/domain/ports.py`).

Read-only view over `seguro_arrendamiento`'s `polizas_arrendamiento` table
— same rationale as `seguro_arrendamiento.infrastructure.persistence.
repository.UsuarioIdentidadRepositoryPostgres` reading `usuarios`' table:
this domain never modifies `PolizaArrendamiento` (proposal.md Impact:
"lectura de PolizaArrendamiento ... sin modificarlo", design.md decisión
5), it only reads `estado` to gate `generar_contrato`'s entry and to link
the resulting `Contrato.poliza_id`.

Kept in its own module (not alongside `ContratoRepositoryPostgres`/
`ArrendamientoActivoRepositoryPostgres` in `repository.py`) so that file
only ever touches tables `firma_contrato` owns.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from seguro_arrendamiento.infrastructure.persistence.models import PolizaArrendamientoORM

_ESTADO_APROBADA = "aprobada"


class PolizaArrendamientoRepositoryPostgres:
    """Postgres-backed adapter for `PolizaArrendamientoPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_poliza_aprobada(self, usuario_id: UUID) -> UUID | None:
        """Return the `id` of an approved `PolizaArrendamiento` belonging
        to `usuario_id`, or `None` if it has none."""
        query = select(PolizaArrendamientoORM.id).where(
            PolizaArrendamientoORM.usuario_id == usuario_id,
            PolizaArrendamientoORM.estado == _ESTADO_APROBADA,
        )
        resultado = await self._session.execute(query)
        return resultado.scalars().first()
