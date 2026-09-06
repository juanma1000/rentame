"""HTTP API for the `firma-contrato` domain (tasks 6.2/6.4 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

`POST /firma-contrato/generar` and `POST /firma-contrato/webhook` only
orchestrate: they map the request into a command/`ResultadoFirmaWebhook`,
call the corresponding use case (real Postgres-backed repositories,
injected via `Depends`), and map the resulting domain entity to a response
schema. No business rule is re-implemented at this layer — same precedent
as `seguro_arrendamiento/infrastructure/api/router.py`.

`firma_contrato.domain.exceptions.PolizaNoAprobada`,
`ContratoNoEnviadoAFirma` and
`firma_contrato.application.procesar_resultado_firma.ContratoNoEncontrado`
are not caught here — they propagate to the app-level exception handlers
registered in `main.py`, same convention as every other domain exception
handler.

`POST /firma-contrato/webhook` has no auth dependency: it is called by the
proveedor externo (Viafirma), not by an authenticated user of this app —
same rationale payment-gateway webhooks use elsewhere (out of scope here,
but a documented precedent this domain follows). Validating the call is
genuinely from Viafirma (e.g. a signature header) is left to
`ViafirmaAdapter`'s real integration (task 7.2's open question), not to
this router.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from firma_contrato.application.consultar_estado_firma import consultar_estado_firma
from firma_contrato.application.generar_contrato import GenerarContratoCommand, generar_contrato
from firma_contrato.application.procesar_resultado_firma import procesar_resultado_firma
from firma_contrato.domain.ports import ProveedorFirmaElectronicaPort, ResultadoFirmaWebhook
from firma_contrato.infrastructure.api.schemas import (
    ContratoResponse,
    EstadoFirmaResponse,
    GenerarContratoRequest,
    WebhookFirmaRequest,
)
from firma_contrato.infrastructure.persistence.poliza_arrendamiento_repository import (
    PolizaArrendamientoRepositoryPostgres,
)
from firma_contrato.infrastructure.persistence.repository import (
    ArrendamientoActivoRepositoryPostgres,
    ContratoRepositoryPostgres,
)
from firma_contrato.infrastructure.proveedor import get_proveedor_firma_electronica
from shared.infrastructure.auth.dependencies import get_current_inquilino
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session

router = APIRouter(prefix="/firma-contrato", tags=["firma-contrato"])


def get_contrato_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ContratoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return ContratoRepositoryPostgres(session)


def get_arrendamiento_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArrendamientoActivoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return ArrendamientoActivoRepositoryPostgres(session)


def get_poliza_arrendamiento_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PolizaArrendamientoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return PolizaArrendamientoRepositoryPostgres(session)


CurrentInquilino = Annotated[TokenPayload, Depends(get_current_inquilino)]
ContratoRepository = Annotated[ContratoRepositoryPostgres, Depends(get_contrato_repository)]
ArrendamientoRepository = Annotated[
    ArrendamientoActivoRepositoryPostgres, Depends(get_arrendamiento_repository)
]
PolizaArrendamientoRepository = Annotated[
    PolizaArrendamientoRepositoryPostgres, Depends(get_poliza_arrendamiento_repository)
]
Proveedor = Annotated[ProveedorFirmaElectronicaPort, Depends(get_proveedor_firma_electronica)]


@router.post(
    "/generar",
    status_code=status.HTTP_200_OK,
    response_model=ContratoResponse,
)
async def generar_contrato_endpoint(
    current_inquilino: CurrentInquilino,
    contrato_repository: ContratoRepository,
    poliza_arrendamiento_repository: PolizaArrendamientoRepository,
    proveedor: Proveedor,
    request: GenerarContratoRequest,
) -> ContratoResponse:
    """`POST /firma-contrato/generar` — an inquilino with an approved
    `PolizaArrendamiento` requests the generation of their contrato de
    arrendamiento.

    Rejects (`PolizaNoAprobada` -> `403`, mapped in `main.py`) when the
    account has no `PolizaArrendamiento` in estado `aprobada` — no document
    is generated and the proveedor is never called in that case.
    """
    command = GenerarContratoCommand(
        usuario_id=uuid.UUID(current_inquilino.sub),
        inmueble_id=request.inmueble_id,
        nombre_inquilino=request.nombre_inquilino,
        nombre_propietario=request.nombre_propietario,
        direccion_inmueble=request.direccion_inmueble,
        canon_mensual=request.canon_mensual,
        duracion_meses=request.duracion_meses,
    )
    contrato = await generar_contrato(
        command,
        contrato_repository=contrato_repository,
        poliza_arrendamiento=poliza_arrendamiento_repository,
        proveedor=proveedor,
    )
    return ContratoResponse.from_domain(contrato)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    response_model=ContratoResponse,
)
async def webhook_firma_endpoint(
    contrato_repository: ContratoRepository,
    arrendamiento_repository: ArrendamientoRepository,
    request: WebhookFirmaRequest,
) -> ContratoResponse:
    """`POST /firma-contrato/webhook` — the proveedor de firma electrónica
    reports the resultado (firmado/rechazado/expirado) of a previously
    enviado-a-firma contrato.

    Rejects (`ContratoNoEncontrado` -> `404`, `ContratoNoEnviadoAFirma` ->
    `409`, both mapped in `main.py`) when the referencia does not match any
    contrato, or the matched contrato is not currently `enviado_a_firma`.
    """
    resultado = ResultadoFirmaWebhook(
        referencia_externa=request.referencia_externa,
        estado=request.estado,
    )
    contrato = await procesar_resultado_firma(
        resultado,
        contrato_repository=contrato_repository,
        arrendamiento_repository=arrendamiento_repository,
    )
    return ContratoResponse.from_domain(contrato)


@router.get("/estado", status_code=status.HTTP_200_OK, response_model=EstadoFirmaResponse)
async def consultar_estado_firma_endpoint(
    current_inquilino: CurrentInquilino,
    contrato_repository: ContratoRepository,
    arrendamiento_repository: ArrendamientoRepository,
) -> EstadoFirmaResponse:
    """`GET /firma-contrato/estado` — read-only: returns the current
    inquilino's firma-contrato estado (`"no_iniciado"` if no `Contrato`
    exists, otherwise the most recent one's estado plus the
    `arrendamiento_activo_id` when it is `firmado`), so the
    `frontend-flujo-arrendamiento` wizard can know which step it is on
    without depending on error codes from `POST /firma-contrato/generar`.

    Never creates or modifies any record, and never calls `proveedor` —
    same rationale as `consultar_estado_firma`'s own docstring.
    """
    resultado = await consultar_estado_firma(
        uuid.UUID(current_inquilino.sub),
        contrato_repository=contrato_repository,
        arrendamiento_repository=arrendamiento_repository,
    )
    return EstadoFirmaResponse(
        estado=resultado.estado,
        arrendamiento_activo_id=resultado.arrendamiento_activo_id,
    )
