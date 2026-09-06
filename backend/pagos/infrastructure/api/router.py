"""HTTP API for the `pagos` domain (tasks 7.2/7.4/7.6 of
`openspec/changes/pago-mensual-renta/tasks.md`).

`POST /pagos/{pago_id}/iniciar`, `POST /pagos/webhook` and
`GET /arrendamientos/{arrendamiento_activo_id}/pagos` only orchestrate:
they map the request into a use-case call (real Postgres-backed
repositories, injected via `Depends`) and map the resulting domain
entity/entities to a response schema. No business rule is
re-implemented at this layer — same precedent as
`firma_contrato/infrastructure/api/router.py`.

This router carries no single fixed `prefix` because it exposes routes
under two different resources (`/pagos/...` and
`/arrendamientos/{id}/pagos`) — same pattern would apply to any domain
whose read model spans more than one URL namespace; every path is
declared in full on each route instead.

`pagos.domain.exceptions.PagoNoEncontrado`, `PagoYaCompletado`,
`ArrendamientoActivoNoEncontrado` and `CobroPagoNoDisponible` are not
caught here — they propagate to the app-level exception handlers
registered in `main.py`, same convention as every other domain exception
handler.

`POST /pagos/webhook` has no auth dependency: it is called by the
pasarela externa (Wompi), not by an authenticated user of this app — same
convention `firma_contrato`'s `/webhook` uses.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from pagos.application.iniciar_pago import iniciar_pago
from pagos.application.procesar_resultado_pago import procesar_resultado_pago
from pagos.domain.ports import PasarelaPagosPort, ResultadoWebhookPago
from pagos.infrastructure.api.schemas import (
    HistorialPagosResponse,
    PagoResponse,
    WebhookPagoRequest,
)
from pagos.infrastructure.persistence.arrendamiento_activo_repository import (
    ArrendamientoActivoRepositoryPostgres,
)
from pagos.infrastructure.persistence.inmueble_repository import InmuebleRepositoryPostgres
from pagos.infrastructure.persistence.poliza_arrendamiento_repository import (
    PolizaArrendamientoRepositoryPostgres,
)
from pagos.infrastructure.persistence.repository import PagoRepositoryPostgres
from pagos.infrastructure.proveedor import get_pasarela_pagos
from shared.infrastructure.auth.dependencies import get_current_inquilino
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session

router = APIRouter(tags=["pagos"])


def get_pago_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PagoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return PagoRepositoryPostgres(session)


def get_arrendamiento_activo_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArrendamientoActivoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return ArrendamientoActivoRepositoryPostgres(session)


def get_poliza_arrendamiento_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PolizaArrendamientoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return PolizaArrendamientoRepositoryPostgres(session)


def get_inmueble_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InmuebleRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return InmuebleRepositoryPostgres(session)


CurrentInquilino = Annotated[TokenPayload, Depends(get_current_inquilino)]
PagoRepository = Annotated[PagoRepositoryPostgres, Depends(get_pago_repository)]
ArrendamientoActivoRepository = Annotated[
    ArrendamientoActivoRepositoryPostgres, Depends(get_arrendamiento_activo_repository)
]
PolizaArrendamientoRepository = Annotated[
    PolizaArrendamientoRepositoryPostgres, Depends(get_poliza_arrendamiento_repository)
]
InmuebleRepository = Annotated[InmuebleRepositoryPostgres, Depends(get_inmueble_repository)]
Pasarela = Annotated[PasarelaPagosPort, Depends(get_pasarela_pagos)]


@router.post(
    "/pagos/{pago_id}/iniciar",
    status_code=status.HTTP_200_OK,
    response_model=PagoResponse,
)
async def iniciar_pago_endpoint(
    pago_id: uuid.UUID,
    current_inquilino: CurrentInquilino,
    pago_repository: PagoRepository,
    arrendamiento_activo_repository: ArrendamientoActivoRepository,
    poliza_arrendamiento_repository: PolizaArrendamientoRepository,
    inmueble_repository: InmuebleRepository,
    pasarela: Pasarela,
) -> PagoResponse:
    """`POST /pagos/{pago_id}/iniciar` — an inquilino starts the cobro of
    a `Pago` pendiente (modelo pull, spec.md: "El inquilino inicia el
    pago").

    Rejects (`PagoNoEncontrado` -> `404`, `PagoYaCompletado` -> `409`,
    both mapped in `main.py`) when the pago does not exist or is already
    `completado` — the pasarela is never called in the latter case.
    """
    pago = await iniciar_pago(
        pago_id,
        pago_repository=pago_repository,
        arrendamiento_activo=arrendamiento_activo_repository,
        poliza_arrendamiento=poliza_arrendamiento_repository,
        inmueble=inmueble_repository,
        pasarela=pasarela,
    )
    return PagoResponse.from_domain(pago)


@router.post(
    "/pagos/webhook",
    status_code=status.HTTP_200_OK,
    response_model=PagoResponse,
)
async def webhook_pago_endpoint(
    pago_repository: PagoRepository,
    request: WebhookPagoRequest,
) -> PagoResponse:
    """`POST /pagos/webhook` — the pasarela de pagos reports the resultado
    (`completado`/`fallido`) of a previously-iniciado cobro.

    Rejects (`PagoNoEncontrado` -> `404`, mapped in `main.py`) when the
    referencia does not match any pago.
    """
    resultado = ResultadoWebhookPago(
        referencia_externa=request.referencia_externa,
        estado=request.estado,
    )
    pago = await procesar_resultado_pago(resultado, pago_repository=pago_repository)
    return PagoResponse.from_domain(pago)


@router.get(
    "/arrendamientos/{arrendamiento_activo_id}/pagos",
    status_code=status.HTTP_200_OK,
    response_model=HistorialPagosResponse,
)
async def historial_pagos_endpoint(
    arrendamiento_activo_id: uuid.UUID,
    current_inquilino: CurrentInquilino,
    pago_repository: PagoRepository,
) -> HistorialPagosResponse:
    """`GET /arrendamientos/{arrendamiento_activo_id}/pagos` — the full
    historial de pagos for that arrendamiento, in any estado (spec.md:
    "sin filtrar por estado")."""
    pagos = await pago_repository.listar_por_arrendamiento(arrendamiento_activo_id)
    return HistorialPagosResponse(pagos=[PagoResponse.from_domain(pago) for pago in pagos])
