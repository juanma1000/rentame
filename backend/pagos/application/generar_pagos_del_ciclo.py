"""`generar_pagos_del_ciclo` use case, invoked by the monthly job
(task 9's ECS/Fargate one-off task, `pagos/infrastructure/jobs/`).

Orchestrates the "Generación automática del pago pendiente por ciclo"
requirement of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md` (task 3.1-3.2 of
`openspec/changes/pago-mensual-renta/tasks.md`).

Per design.md decisión 4, this use case is invoked by a separate one-off
process (not an in-app scheduler) precisely so it can run more than once
against the same ciclo without side effects — idempotency here is not an
optimization, it is the mechanism that makes a separate, possibly-retried
invocation safe: `PagoRepositoryPort.obtener_pendiente_por_arrendamiento`
is checked before creating each `Pago`, and an `ArrendamientoActivo` that
already has an unresolved (`pendiente`) `Pago` is skipped.

`monto` comes from `Inmueble.valor_mensual` (via `InmueblePort`), not from
`PolizaArrendamiento.prima_mensual` — see `pagos/domain/ports.py`'s
`InmueblePort` docstring for why `Inmueble.valor_mensual` is the only
surviving source for the canon mensual by the time an `ArrendamientoActivo`
exists.

`DIAS_PLAZO_PAGO` fixes design.md's open question ("Duración exacta del
ciclo de facturación y cómo se calcula la fecha límite... se resuelve al
implementar generar_pagos_del_ciclo") with the simplest reasonable rule
for an MVP job that runs once a month: a fixed grace period counted from
the day the job runs, not from `ArrendamientoActivo.fecha_inicio` (which
would require tracking which ciclo-month each `Pago` belongs to — out of
scope per design.md's open questions, deferred to a future change on
mora/penalidades).
"""

from __future__ import annotations

from datetime import date, timedelta

from pagos.domain.pago import Pago
from pagos.domain.ports import ArrendamientoActivoPort, InmueblePort, PagoRepositoryPort

DIAS_PLAZO_PAGO = 5


async def generar_pagos_del_ciclo(
    *,
    arrendamiento_activo: ArrendamientoActivoPort,
    inmueble: InmueblePort,
    pago_repository: PagoRepositoryPort,
) -> list[Pago]:
    """Run one invocation of the monthly Pago-generation job.

    For every currently-active `ArrendamientoActivo`, creates a `Pago`
    `pendiente` (monto = `Inmueble.valor_mensual`, fecha_limite = today +
    `DIAS_PLAZO_PAGO`) unless one already exists unresolved for that
    arrendamiento — safe to invoke more than once for the same ciclo
    (spec.md: "El proceso mensual no duplica pagos si se ejecuta más de
    una vez").

    An `ArrendamientoActivo` whose `Inmueble` cannot be resolved (a
    referential-integrity condition that should not happen in practice) is
    skipped rather than aborting the whole batch, so one broken record
    never blocks every other arrendamiento's Pago from being generated.

    Returns the list of newly-created `Pago`s (empty when every active
    arrendamiento already has one pendiente).
    """
    creados: list[Pago] = []
    for activo in await arrendamiento_activo.listar_activos():
        pendiente = await pago_repository.obtener_pendiente_por_arrendamiento(activo.id)
        if pendiente is not None:
            continue

        inmueble_info = await inmueble.obtener(activo.inmueble_id)
        if inmueble_info is None:
            continue

        pago = Pago.crear(
            arrendamiento_activo_id=activo.id,
            monto=inmueble_info.valor_mensual,
            fecha_limite=date.today() + timedelta(days=DIAS_PLAZO_PAGO),
        )
        creados.append(await pago_repository.guardar(pago))

    return creados
