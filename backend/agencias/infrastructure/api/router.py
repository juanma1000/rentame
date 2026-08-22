"""HTTP API for the `agencias` domain (tasks 7.1-7.8 of
`openspec/changes/hu-007/tasks.md`).

Every endpoint only orchestrates: it maps the HTTP request/JWT into the
corresponding use case's command, calls the use case (real Postgres-backed
repositories, injected via `Depends`), and maps the resulting domain entity
(or list of them) to its `*Response` schema. No business rule is
re-implemented at this layer — that is the precedent already set by
`inmuebles/infrastructure/api/router.py`.

Domain exceptions (`AgenteYaTieneAgencia`, `SolicitudNoEncontrada`,
`RelacionNoEncontrada`, `AgenteNoEsMiembroDeAgencia`,
`UltimoAgenteConRelacionesActivas`, `PropietarioInvalido`) are not caught
here — they propagate to the app-level exception handlers registered in
`main.py`, which map them to 409/404/404/403/409/403 respectively with a
`{"detail": "<message>"}` body, per the contract fixed by
`tests/agencias/infrastructure/test_api.py`. `PropietarioInvalido` here is
`agencias.domain.exceptions.PropietarioInvalido` — a distinct class from
`inmuebles.domain.exceptions.PropietarioInvalido`, both registered under
different handler names in `main.py`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agencias.application.aprobar_ingreso import AprobarIngresoCommand, aprobar_ingreso
from agencias.application.buscar_agencias import BuscarAgenciasCommand, buscar_agencias
from agencias.application.confirmar_relacion import ConfirmarRelacionCommand, confirmar_relacion
from agencias.application.crear_agencia import CrearAgenciaCommand, crear_agencia
from agencias.application.iniciar_relacion import IniciarRelacionCommand, iniciar_relacion
from agencias.application.reasignar_responsable import (
    ReasignarResponsableCommand,
    reasignar_responsable,
)
from agencias.application.revocar_relacion import RevocarRelacionCommand, revocar_relacion
from agencias.application.salir_de_agencia import SalirDeAgenciaCommand, salir_de_agencia
from agencias.application.solicitar_ingreso import SolicitarIngresoCommand, solicitar_ingreso
from agencias.infrastructure.api.schemas import (
    AgenciaBuscarResponse,
    AgenciaCreateRequest,
    AgenciaResponse,
    ReasignarResponsableRequest,
    RelacionResponse,
    SolicitudIngresoResponse,
)
from agencias.infrastructure.persistence.repository import (
    AgenciaRepositoryPostgres,
    RelacionRepositoryPostgres,
    SolicitudIngresoRepositoryPostgres,
    UsuarioAgenciaRepositoryPostgres,
)
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from shared.infrastructure.auth.dependencies import get_current_agente, get_current_propietario
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session
from usuarios.infrastructure.persistence.models import UsuarioORM

router = APIRouter(prefix="/agencias", tags=["agencias"])


def get_agencia_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgenciaRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return AgenciaRepositoryPostgres(session)


def get_relacion_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RelacionRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return RelacionRepositoryPostgres(session)


def get_solicitud_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SolicitudIngresoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return SolicitudIngresoRepositoryPostgres(session)


def get_usuario_agencia_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsuarioAgenciaRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return UsuarioAgenciaRepositoryPostgres(session)


def get_inmueble_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InmuebleRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`.

    Needed by the despublicación cascade triggered from `confirmar`/
    `revocar` (design.md decisión 4) — the `agencias` API depends on the
    `inmuebles` domain's real repository, same as the `agencias` application
    layer already does.
    """
    return InmuebleRepositoryPostgres(session)


CurrentAgente = Annotated[TokenPayload, Depends(get_current_agente)]
CurrentPropietario = Annotated[TokenPayload, Depends(get_current_propietario)]
AgenciaRepository = Annotated[AgenciaRepositoryPostgres, Depends(get_agencia_repository)]
RelacionRepository = Annotated[RelacionRepositoryPostgres, Depends(get_relacion_repository)]
SolicitudRepository = Annotated[
    SolicitudIngresoRepositoryPostgres, Depends(get_solicitud_repository)
]
UsuarioAgenciaRepository = Annotated[
    UsuarioAgenciaRepositoryPostgres, Depends(get_usuario_agencia_repository)
]
InmuebleRepository = Annotated[InmuebleRepositoryPostgres, Depends(get_inmueble_repository)]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AgenciaResponse)
async def crear_agencia_endpoint(
    payload: AgenciaCreateRequest,
    current_agente: CurrentAgente,
    agencia_repository: AgenciaRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> AgenciaResponse:
    """`POST /agencias/` — create an agencia, linking the creating agente as
    its first member. Rejects (`AgenteYaTieneAgencia` -> 409) when the agente
    already belongs to one."""
    command = CrearAgenciaCommand(
        razon_social=payload.razon_social,
        nit=payload.nit,
        agente_id=uuid.UUID(current_agente.sub),
    )
    agencia = await crear_agencia(
        command, agencia_repository=agencia_repository, usuario_repository=usuario_repository
    )
    return AgenciaResponse.from_domain(agencia)


@router.post(
    "/{agencia_id}/solicitudes",
    status_code=status.HTTP_201_CREATED,
    response_model=SolicitudIngresoResponse,
)
async def solicitar_ingreso_endpoint(
    agencia_id: uuid.UUID,
    current_agente: CurrentAgente,
    solicitud_repository: SolicitudRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> SolicitudIngresoResponse:
    """`POST /agencias/{agencia_id}/solicitudes` — an agente sin agencia
    requests to join `agencia_id`."""
    command = SolicitarIngresoCommand(
        agencia_id=agencia_id, agente_id=uuid.UUID(current_agente.sub)
    )
    solicitud = await solicitar_ingreso(
        command, solicitud_repository=solicitud_repository, usuario_repository=usuario_repository
    )
    return SolicitudIngresoResponse.from_domain(solicitud)


@router.post(
    "/solicitudes/{solicitud_id}/aprobar",
    response_model=SolicitudIngresoResponse,
)
async def aprobar_ingreso_endpoint(
    solicitud_id: uuid.UUID,
    current_agente: CurrentAgente,
    solicitud_repository: SolicitudRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> SolicitudIngresoResponse:
    """`POST /agencias/solicitudes/{solicitud_id}/aprobar` — a member of the
    solicitud's agencia approves it, linking the solicitante as a member.
    Rejects (`AgenteNoEsMiembroDeAgencia` -> 403) when the approver is not a
    member of that agencia."""
    command = AprobarIngresoCommand(
        solicitud_id=solicitud_id, aprobador_id=uuid.UUID(current_agente.sub)
    )
    solicitud = await aprobar_ingreso(
        command, solicitud_repository=solicitud_repository, usuario_repository=usuario_repository
    )
    return SolicitudIngresoResponse.from_domain(solicitud)


@router.post("/salir", status_code=status.HTTP_204_NO_CONTENT)
async def salir_de_agencia_endpoint(
    current_agente: CurrentAgente,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> Response:
    """`POST /agencias/salir` — the authenticated agente leaves their
    agencia. Rejects (`UltimoAgenteConRelacionesActivas` -> 409) when they
    are the last member of an agencia with at least one relación `activa`."""
    agente_id = uuid.UUID(current_agente.sub)
    agencia_id = await usuario_repository.obtener_agencia_id(agente_id)
    if agencia_id is not None:
        command = SalirDeAgenciaCommand(agencia_id=agencia_id, agente_id=agente_id)
        await salir_de_agencia(
            command,
            relacion_repository=relacion_repository,
            usuario_repository=usuario_repository,
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{agencia_id}/relaciones",
    status_code=status.HTTP_201_CREATED,
    response_model=RelacionResponse,
)
async def iniciar_relacion_endpoint(
    agencia_id: uuid.UUID,
    current_propietario: CurrentPropietario,
    relacion_repository: RelacionRepository,
) -> RelacionResponse:
    """`POST /agencias/{agencia_id}/relaciones` — a propietario starts a
    `pendiente` relación with `agencia_id`."""
    command = IniciarRelacionCommand(
        agencia_id=agencia_id, propietario_id=uuid.UUID(current_propietario.sub)
    )
    relacion = await iniciar_relacion(command, relacion_repository=relacion_repository)
    return RelacionResponse.from_domain(relacion)


@router.post("/relaciones/{relacion_id}/confirmar", response_model=RelacionResponse)
async def confirmar_relacion_endpoint(
    relacion_id: uuid.UUID,
    current_agente: CurrentAgente,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
    inmueble_repository: InmuebleRepository,
) -> RelacionResponse:
    """`POST /agencias/relaciones/{relacion_id}/confirmar` — a member of the
    relación's agencia activates it, auto-revoking any previous `activa`
    relación of the same propietario (running the despublicación cascade).
    Rejects (`AgenteNoEsMiembroDeAgencia` -> 403) when the confirming agente
    is not a member."""
    command = ConfirmarRelacionCommand(
        relacion_id=relacion_id, agente_id=uuid.UUID(current_agente.sub)
    )
    relacion = await confirmar_relacion(
        command,
        relacion_repository=relacion_repository,
        usuario_repository=usuario_repository,
        inmueble_repository=inmueble_repository,
    )
    return RelacionResponse.from_domain(relacion)


@router.post("/relaciones/{relacion_id}/revocar", response_model=RelacionResponse)
async def revocar_relacion_endpoint(
    relacion_id: uuid.UUID,
    current_propietario: CurrentPropietario,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
    inmueble_repository: InmuebleRepository,
) -> RelacionResponse:
    """`POST /agencias/relaciones/{relacion_id}/revocar` — the propietario
    revokes their own relación (no agencia-side approval required),
    running the despublicación cascade. Rejects (`PropietarioInvalido` ->
    403) when the caller is not the relación's own propietario."""
    command = RevocarRelacionCommand(
        relacion_id=relacion_id, propietario_id=uuid.UUID(current_propietario.sub)
    )
    relacion = await revocar_relacion(
        command,
        relacion_repository=relacion_repository,
        usuario_repository=usuario_repository,
        inmueble_repository=inmueble_repository,
    )
    return RelacionResponse.from_domain(relacion)


@router.patch("/relaciones/{relacion_id}/responsable", response_model=RelacionResponse)
async def reasignar_responsable_endpoint(
    relacion_id: uuid.UUID,
    payload: ReasignarResponsableRequest,
    current_agente: CurrentAgente,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> RelacionResponse:
    """`PATCH /agencias/relaciones/{relacion_id}/responsable` — reassign the
    relación's `agente_responsable_id`. Rejects
    (`AgenteNoEsMiembroDeAgencia` -> 403) when either the caller or
    `nuevo_agente_id` is not a member of the relación's agencia."""
    command = ReasignarResponsableCommand(
        relacion_id=relacion_id,
        solicitante_id=uuid.UUID(current_agente.sub),
        nuevo_agente_id=payload.nuevo_agente_id,
    )
    relacion = await reasignar_responsable(
        command, relacion_repository=relacion_repository, usuario_repository=usuario_repository
    )
    return RelacionResponse.from_domain(relacion)


@router.get("/buscar", response_model=list[AgenciaBuscarResponse])
async def buscar_agencias_endpoint(
    q: str,
    agencia_repository: AgenciaRepository,
) -> list[AgenciaBuscarResponse]:
    """`GET /agencias/buscar?q=<texto>` — public endpoint (no `Depends` auth):
    search agencias by partial `razon_social`/`nit`, case-insensitive.
    Returns only public fields; empty list when there is no match."""
    command = BuscarAgenciasCommand(texto=q)
    agencias = await buscar_agencias(command, agencia_repository=agencia_repository)
    return [AgenciaBuscarResponse.from_domain(agencia) for agencia in agencias]


@router.get("/mia/propietarios", response_model=list[RelacionResponse])
async def listar_mis_propietarios_endpoint(
    current_agente: CurrentAgente,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[RelacionResponse]:
    """`GET /agencias/mia/propietarios` — every relación of the authenticated
    agente's agencia (empty list when the agencia has none, or the agente
    belongs to no agencia).

    Each item's `propietario_email` (hu-002 task 6.5) is resolved here from
    `usuario.email` so the frontend can render a readable propietario
    selector when publishing an inmueble on their behalf (task 11.x) —
    `agencias/application` and `agencias/domain` are not touched for this,
    only this API-layer response schema/endpoint."""
    agencia_id = await usuario_repository.obtener_agencia_id(uuid.UUID(current_agente.sub))
    if agencia_id is None:
        return []

    relaciones = await relacion_repository.listar_por_agencia(agencia_id)
    if not relaciones:
        return []

    propietario_ids = [relacion.propietario_id for relacion in relaciones]
    resultado = await session.execute(
        select(UsuarioORM.id, UsuarioORM.email).where(UsuarioORM.id.in_(propietario_ids))
    )
    emails_por_id = {fila.id: fila.email for fila in resultado}

    return [
        RelacionResponse.from_domain(
            relacion, propietario_email=emails_por_id.get(relacion.propietario_id)
        )
        for relacion in relaciones
    ]
