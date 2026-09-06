"""Entrypoint for the monthly `pagos` job, run as a one-off ECS/Fargate
task (`infra/aws/pagos-mensuales-task/`), never as an in-app scheduler —
per design.md decisión 4, the backend runs multiple autoscaled replicas
(App Runner), and an in-app scheduler would run once per replica,
generating duplicate `Pago`s for the same `ArrendamientoActivo`/ciclo. A
separate task, triggered once by an external schedule (EventBridge),
avoids that: same rationale documented for `alembic upgrade head` in
`backend/docker-entrypoint.sh` and `infra/aws/migrations-task/`.

`generar_pagos_del_ciclo` (`pagos/application/generar_pagos_del_ciclo.py`)
is itself idempotent — running this script twice in the same ciclo is
safe (task 9.2's integration test asserts exactly this) — so this
entrypoint adds no locking of its own; it only wires the use case to real
Postgres-backed repositories and commits.

Run with:
    docker compose exec backend python scripts/generar_pagos_mensuales.py
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from pagos.application.generar_pagos_del_ciclo import generar_pagos_del_ciclo
from pagos.domain.pago import Pago
from pagos.infrastructure.persistence.arrendamiento_activo_repository import (
    ArrendamientoActivoRepositoryPostgres,
)
from pagos.infrastructure.persistence.inmueble_repository import InmuebleRepositoryPostgres
from pagos.infrastructure.persistence.repository import PagoRepositoryPostgres
from shared.infrastructure.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pagos.generar_pagos_mensuales")


async def generar_pagos_mensuales(session: AsyncSession) -> list[Pago]:
    """Wire `generar_pagos_del_ciclo` to real Postgres-backed repositories
    bound to `session`, without committing — the caller (`main`, or a
    test's own transaction-scoped fixture) owns the commit/rollback
    boundary, same convention as every other repository in this project.

    Kept separate from `main()` so integration tests (task 9.2) can drive
    this exact wiring against the test database via the `db_session`
    fixture, instead of `main()`'s own `AsyncSessionLocal` (bound to
    `settings.database_url`, the dev/prod database).
    """
    return await generar_pagos_del_ciclo(
        arrendamiento_activo=ArrendamientoActivoRepositoryPostgres(session),
        inmueble=InmuebleRepositoryPostgres(session),
        pago_repository=PagoRepositoryPostgres(session),
    )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        pagos_creados = await generar_pagos_mensuales(session)
        await session.commit()

    logger.info(
        "generar_pagos_del_ciclo: %d Pago(s) pendiente(s) creado(s)",
        len(pagos_creados),
    )


if __name__ == "__main__":
    asyncio.run(main())
