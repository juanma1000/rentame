"""Integration tests for the `seguro-arrendamiento` persistence adapters
(task 4.1 of `openspec/changes/seguro-arrendamiento-inquilino/tasks.md`),
against a real PostgreSQL test database (`db_session`/`seed_inquilino` from
`backend/tests/conftest.py`) — no mocks, following the precedent of
`tests/identidad/infrastructure/test_repository.py`.

TDD Red phase:
`seguro_arrendamiento/infrastructure/persistence/models.py` and
`repository.py` do not exist yet, so every test here is expected to fail
with `ModuleNotFoundError` until `backend-expert` implements them (task
4.2). This file fixes, by construction, the contract to satisfy:

- `PolizaArrendamientoRepositoryPostgres.guardar(poliza)` inserts a new
  row into `polizas_arrendamiento` and returns the domain entity with `id`
  set — never persisting raw document bytes (they never reach this layer
  in the first place, per spec.md).
- `PolizaArrendamientoRepositoryPostgres.listar_por_usuario(usuario_id)`
  returns every `PolizaArrendamiento` for that account, empty list if none.
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

# Imported so `AgenciaORM` registers on `Base.metadata` before this module's
# tests create the schema — same requirement documented in
# `tests/identidad/infrastructure/test_repository.py`.
from agencias.infrastructure.persistence.models import AgenciaORM  # noqa: F401
from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza, PolizaArrendamiento
from seguro_arrendamiento.infrastructure.persistence.repository import (
    PolizaArrendamientoRepositoryPostgres,
)
from usuarios.infrastructure.persistence.models import UsuarioORM


class TestPolizaArrendamientoRepositoryPostgres:
    async def test_guardar_inserts_and_returns_poliza_with_id(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PolizaArrendamientoRepositoryPostgres(db_session)
        poliza = PolizaArrendamiento.solicitar(usuario_id=seed_inquilino.id)
        poliza.aprobar(
            prima_mensual=45000.0,
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2027, 1, 1),
            referencia_externa="ext-ref-1",
        )

        # Act
        guardada = await repository.guardar(poliza)

        # Assert
        assert guardada.id is not None
        assert guardada.usuario_id == seed_inquilino.id
        assert guardada.estado == EstadoPoliza.APROBADA
        assert guardada.prima_mensual == 45000.0
        assert guardada.vigencia_desde == date(2026, 1, 1)
        assert guardada.vigencia_hasta == date(2027, 1, 1)
        assert guardada.referencia_externa == "ext-ref-1"

    async def test_listar_por_usuario_returns_every_poliza_for_that_account(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PolizaArrendamientoRepositoryPostgres(db_session)
        primera = PolizaArrendamiento.solicitar(usuario_id=seed_inquilino.id)
        primera.rechazar(referencia_externa="ext-ref-rechazo")
        await repository.guardar(primera)

        segunda = PolizaArrendamiento.solicitar(usuario_id=seed_inquilino.id)
        segunda.aprobar(
            prima_mensual=45000.0,
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2027, 1, 1),
            referencia_externa="ext-ref-aprobada",
        )
        await repository.guardar(segunda)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert len(resultado) == 2
        estados = {p.estado for p in resultado}
        assert estados == {EstadoPoliza.RECHAZADA, EstadoPoliza.APROBADA}

    async def test_listar_por_usuario_returns_empty_list_when_no_polizas(
        self, db_session: AsyncSession, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange
        repository = PolizaArrendamientoRepositoryPostgres(db_session)

        # Act
        resultado = await repository.listar_por_usuario(seed_inquilino.id)

        # Assert
        assert resultado == []
