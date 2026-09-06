"""Postgres-backed adapters for the `seguro-arrendamiento` domain ports
(`seguro_arrendamiento/domain/ports.py`).

Follows the `ValidacionIdentidadRepositoryPostgres`/
`UsuarioIdentidadRepositoryPostgres` precedent
(`identidad/infrastructure/persistence/repository.py`): every constructor
takes an injected `AsyncSession` (no commit/rollback management here —
that's the caller's/unit-of-work's job), and every method maps between the
domain entities and the persistence models in both directions, so the
domain layer never depends on SQLAlchemy.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza, PolizaArrendamiento
from seguro_arrendamiento.infrastructure.persistence.models import PolizaArrendamientoORM
from usuarios.infrastructure.persistence.models import UsuarioORM


class PolizaArrendamientoRepositoryPostgres:
    """Postgres-backed adapter for `PolizaArrendamientoRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, poliza: PolizaArrendamiento) -> PolizaArrendamiento:
        """Insert a new `PolizaArrendamiento` and return it with `id` set."""
        modelo = self._a_orm(poliza)
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def listar_por_usuario(self, usuario_id: UUID) -> list[PolizaArrendamiento]:
        """Return every `PolizaArrendamiento` belonging to `usuario_id`
        (empty list if it has none)."""
        query = select(PolizaArrendamientoORM).where(
            PolizaArrendamientoORM.usuario_id == usuario_id
        )
        resultado = await self._session.execute(query)
        modelos = resultado.scalars().all()
        return [self._a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _a_orm(poliza: PolizaArrendamiento) -> PolizaArrendamientoORM:
        return PolizaArrendamientoORM(
            id=poliza.id,
            usuario_id=poliza.usuario_id,
            estado=poliza.estado.value,
            fecha=poliza.fecha,
            prima_mensual=poliza.prima_mensual,
            vigencia_desde=poliza.vigencia_desde,
            vigencia_hasta=poliza.vigencia_hasta,
            referencia_externa=poliza.referencia_externa,
        )

    @staticmethod
    def _a_dominio(modelo: PolizaArrendamientoORM) -> PolizaArrendamiento:
        return PolizaArrendamiento(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            estado=EstadoPoliza(modelo.estado),
            fecha=modelo.fecha,
            prima_mensual=(
                float(modelo.prima_mensual) if modelo.prima_mensual is not None else None
            ),
            vigencia_desde=modelo.vigencia_desde,
            vigencia_hasta=modelo.vigencia_hasta,
            referencia_externa=modelo.referencia_externa,
        )


class UsuarioIdentidadRepositoryPostgres:
    """Postgres-backed adapter for `UsuarioIdentidadPort`.

    Read-only view over `usuario.identidad_verificada`
    (`usuarios/infrastructure/persistence/models.py`), same rationale as
    `identidad.infrastructure.persistence.repository.
    UsuarioIdentidadRepositoryPostgres` — this domain never modifies the
    flag (proposal.md Impact: "lectura de `usuario.identidad_verificada` ...
    sin modificarlo").
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def esta_verificado(self, usuario_id: UUID) -> bool:
        """Return the current value of `usuario.identidad_verificada`."""
        modelo = await self._session.get(UsuarioORM, usuario_id)
        if modelo is None:
            return False
        return modelo.identidad_verificada
