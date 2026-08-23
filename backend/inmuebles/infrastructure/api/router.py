"""HTTP API for the `inmuebles` domain (tasks 7.3-7.6 of
`openspec/changes/hu-001/tasks.md`, extended by tasks 6.1-6.4 of
`openspec/changes/hu-002/tasks.md`).

`POST`/`PUT`/`PATCH /disponibilidad` accept both "propietario" and "agente"
callers (`get_current_publicador`). `GET /mios` stays propietario-only
(`get_current_propietario`) and `GET /gestionados` is agente-only
(`get_current_agente`), unchanged from their HU-001/HU-002 contracts.

Every endpoint maps the HTTP request/JWT into the corresponding use case's
command, calls the use case, and maps the resulting `Inmueble` (or list of
them) to `InmuebleResponse`. No business rule is re-implemented at this
layer, with one deliberate exception (design.md decisión 1 of hu-002): the
cross-domain authorization of an agente against `agencias` (does the
agente's agencia have an `ACTIVA` relación with the propietario in
question?) lives here, in the API layer, and nowhere in
`inmuebles/application` or `inmuebles/domain` — those must never import from
`agencias`. This router imports `agencias`' concrete Postgres repositories
directly (mirroring how `agencias/infrastructure/api/router.py` already
imports `InmuebleRepositoryPostgres` in the opposite direction) instead of
adding a port to `inmuebles/domain/ports.py`, since the dependency is
API-layer-to-API-layer, not domain-to-domain.

Domain exceptions (`DomainValidationError`, `InmuebleNoEncontrado`,
`PropietarioInvalido`) are not caught here — they propagate to the
app-level exception handlers registered in `main.py`, which map them to
422/404/403 respectively with a `{"detail": "<message>"}` body, per the
contract fixed by `tests/inmuebles/infrastructure/test_api.py`. The
agente-vs-`agencias` authorization checks added here raise `HTTPException`
directly (403/422) instead, since they are router-level cross-domain
decisions, not domain invariants of `inmuebles` itself.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from agencias.domain.relacion_agencia_propietario import EstadoRelacion
from agencias.infrastructure.persistence.repository import (
    RelacionRepositoryPostgres,
    UsuarioAgenciaRepositoryPostgres,
)
from inmuebles.application.cambiar_disponibilidad import (
    CambiarDisponibilidadCommand,
    cambiar_disponibilidad,
)
from inmuebles.application.editar_inmueble import EditarInmuebleCommand, editar_inmueble
from inmuebles.application.listar_inmuebles_gestionados import listar_inmuebles_gestionados
from inmuebles.application.listar_inmuebles_publicos import listar_inmuebles_publicos
from inmuebles.application.listar_mis_inmuebles import (
    ListarMisInmueblesCommand,
    listar_mis_inmuebles,
)
from inmuebles.application.obtener_inmueble_publico import (
    ObtenerInmueblePublicoCommand,
    obtener_inmueble_publico,
)
from inmuebles.application.publicar_inmueble import (
    FotoParaPublicar,
    PublicarInmuebleCommand,
    publicar_inmueble,
)
from inmuebles.domain.exceptions import InmuebleNoEncontrado
from inmuebles.domain.inmueble import EstadoInmueble
from inmuebles.infrastructure.api.schemas import (
    CambiarDisponibilidadRequest,
    InmuebleEditRequest,
    InmueblePublicoListItemResponse,
    InmueblePublicoResponse,
    InmuebleResponse,
)
from inmuebles.infrastructure.external.s3_storage_adapter import S3StorageAdapter
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from shared.infrastructure.auth.dependencies import (
    ROL_AGENTE,
    ROL_PROPIETARIO,
    get_current_agente,
    get_current_propietario,
    get_current_publicador,
)
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session
from shared.infrastructure.settings import get_settings

router = APIRouter(prefix="/inmuebles", tags=["inmuebles"])


def get_inmueble_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InmuebleRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return InmuebleRepositoryPostgres(session)


@lru_cache
def get_storage_adapter() -> S3StorageAdapter:
    """Process-wide `S3StorageAdapter` singleton.

    Cached (mirrors `get_settings`'s pattern) so the underlying boto3 client
    is created once per process instead of on every request.
    """
    return S3StorageAdapter(get_settings())


def get_relacion_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RelacionRepositoryPostgres:
    """Build an `agencias` relación repository bound to the request-scoped
    `AsyncSession` — needed here (hu-002) to authorize agente callers
    against the `agencias` domain."""
    return RelacionRepositoryPostgres(session)


def get_usuario_agencia_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsuarioAgenciaRepositoryPostgres:
    """Build an `agencias` usuario-agencia repository bound to the
    request-scoped `AsyncSession` — same rationale as
    `get_relacion_repository`."""
    return UsuarioAgenciaRepositoryPostgres(session)


CurrentPropietario = Annotated[TokenPayload, Depends(get_current_propietario)]
CurrentAgente = Annotated[TokenPayload, Depends(get_current_agente)]
CurrentPublicador = Annotated[TokenPayload, Depends(get_current_publicador)]
Repository = Annotated[InmuebleRepositoryPostgres, Depends(get_inmueble_repository)]
Storage = Annotated[S3StorageAdapter, Depends(get_storage_adapter)]
RelacionRepository = Annotated[RelacionRepositoryPostgres, Depends(get_relacion_repository)]
UsuarioAgenciaRepository = Annotated[
    UsuarioAgenciaRepositoryPostgres, Depends(get_usuario_agencia_repository)
]


async def _agencia_tiene_relacion_activa(
    agente_id: uuid.UUID,
    propietario_id: uuid.UUID,
    *,
    relacion_repository: RelacionRepositoryPostgres,
    usuario_repository: UsuarioAgenciaRepositoryPostgres,
) -> bool:
    """`True` iff `agente_id`'s agencia has an `ACTIVA` relación with
    `propietario_id` — the shared check behind every agente-authorization
    decision in this router (hu-002, design.md decisión 1)."""
    agencia_id = await usuario_repository.obtener_agencia_id(agente_id)
    if agencia_id is None:
        return False
    relacion = await relacion_repository.obtener_activa_por_propietario(propietario_id)
    return relacion is not None and relacion.agencia_id == agencia_id


async def _autorizar_publicador_sobre_inmueble(
    current_publicador: TokenPayload,
    propietario_id_real: uuid.UUID,
    *,
    relacion_repository: RelacionRepositoryPostgres,
    usuario_repository: UsuarioAgenciaRepositoryPostgres,
) -> None:
    """Raise `HTTPException(403)` unless `current_publicador` is either the
    inmueble's own propietario, or an agente whose agencia has an `ACTIVA`
    relación with that propietario (hu-002: `PUT`/`PATCH` authorization)."""
    caller_id = uuid.UUID(current_publicador.sub)

    if current_publicador.rol == ROL_PROPIETARIO:
        autorizado = caller_id == propietario_id_real
    else:
        autorizado = await _agencia_tiene_relacion_activa(
            caller_id,
            propietario_id_real,
            relacion_repository=relacion_repository,
            usuario_repository=usuario_repository,
        )

    if not autorizado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para operar sobre este inmueble",
        )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=InmuebleResponse)
async def crear_inmueble(
    current_publicador: CurrentPublicador,
    repository: Repository,
    storage: Storage,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
    direccion: Annotated[str, Form()],
    barrio: Annotated[str, Form()],
    ciudad: Annotated[str, Form()],
    tipo: Annotated[str, Form()],
    area_m2: Annotated[Decimal, Form()],
    habitaciones: Annotated[int, Form()],
    banos: Annotated[int, Form()],
    valor_mensual: Annotated[Decimal, Form()],
    descripcion: Annotated[str, Form()],
    fotos: Annotated[list[UploadFile], File()],
    propietario_id: Annotated[uuid.UUID | None, Form()] = None,
) -> InmuebleResponse:
    """`POST /inmuebles/` — create a listing with 1 to `MAX_FOTOS_INMUEBLE`
    photos, starting in `EstadoInmueble.DISPONIBLE`.

    When the caller's role is "propietario" (HU-001, unchanged), the form's
    `propietario_id` (if present) is ignored and `agente_id` is `null` on
    the response. When it is "agente" (hu-002), `propietario_id` becomes
    required (`422` when absent, before any photo is read/uploaded) and
    must belong to a propietario with an `ACTIVA` relación with the
    agente's agencia (`403` otherwise, no inmueble created, no photo
    uploaded); on success the response's `propietario_id` is the
    represented propietario and `agente_id` is the calling agente's id.
    """
    agente_id: uuid.UUID | None = None
    if current_publicador.rol == ROL_AGENTE:
        if propietario_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="propietario_id is required when the caller is an agente",
            )
        agente_id = uuid.UUID(current_publicador.sub)
        if not await _agencia_tiene_relacion_activa(
            agente_id,
            propietario_id,
            relacion_repository=relacion_repository,
            usuario_repository=usuario_repository,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El agente no tiene una relación activa con este propietario",
            )
        propietario_id_real = propietario_id
    else:
        propietario_id_real = uuid.UUID(current_publicador.sub)

    fotos_para_publicar = [
        FotoParaPublicar(contenido=await foto.read(), es_principal=(indice == 0))
        for indice, foto in enumerate(fotos)
    ]

    command = PublicarInmuebleCommand(
        propietario_id=propietario_id_real,
        direccion=direccion,
        barrio=barrio,
        ciudad=ciudad,
        tipo=tipo,
        area_m2=area_m2,
        habitaciones=habitaciones,
        banos=banos,
        valor_mensual=valor_mensual,
        descripcion=descripcion,
        fotos=fotos_para_publicar,
        agente_id=agente_id,
    )

    inmueble = await publicar_inmueble(command, repository=repository, storage=storage)
    return InmuebleResponse.from_domain(inmueble)


@router.get("/publicos", response_model=list[InmueblePublicoListItemResponse])
async def listar_inmuebles_publicos_endpoint(
    repository: Repository,
) -> list[InmueblePublicoListItemResponse]:
    """`GET /inmuebles/publicos` (hu-003) — every listing in estado
    `disponible`, with no authentication required (empty list when none
    are `disponible`).

    Declared before `PUT /{inmueble_id}` and `PATCH
    /{inmueble_id}/disponibilidad`: FastAPI/Starlette matches route
    templates in declaration order, and `/inmuebles/publicos` would
    otherwise be captured by `/inmuebles/{inmueble_id}` (with
    `inmueble_id="publicos"`), returning 405 instead of reaching this
    handler.
    """
    inmuebles = await listar_inmuebles_publicos(repository=repository)
    return [InmueblePublicoListItemResponse.from_domain(inmueble) for inmueble in inmuebles]


@router.get("/publicos/{inmueble_id}", response_model=InmueblePublicoResponse)
async def obtener_inmueble_publico_endpoint(
    inmueble_id: uuid.UUID,
    repository: Repository,
) -> InmueblePublicoResponse:
    """`GET /inmuebles/publicos/{inmueble_id}` (hu-003) — full detail of a
    single `disponible` listing, with no authentication required.

    404 when the id does not exist, or exists but is `oculto`/`no_disponible`
    (`obtener_inmueble_publico` already collapses both cases into `None`,
    never leaking existence/data of a non-`disponible` inmueble).
    """
    command = ObtenerInmueblePublicoCommand(inmueble_id=inmueble_id)
    inmueble = await obtener_inmueble_publico(command, repository=repository)
    if inmueble is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inmueble no encontrado")
    return InmueblePublicoResponse.from_domain(inmueble)


@router.put("/{inmueble_id}", response_model=InmuebleResponse)
async def editar_inmueble_endpoint(
    inmueble_id: uuid.UUID,
    payload: InmuebleEditRequest,
    current_publicador: CurrentPublicador,
    repository: Repository,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> InmuebleResponse:
    """`PUT /inmuebles/{inmueble_id}` — edit a listing's data.

    Loads the `Inmueble` first to learn its real `propietario_id`, then
    authorizes either the owning propietario or an agente whose agencia has
    an `ACTIVA` relación with that propietario (403 for anyone else, 404
    when `inmueble_id` does not exist). `agente_id` is never changed by this
    endpoint."""
    inmueble = await repository.obtener_por_id(inmueble_id)
    if inmueble is None:
        raise InmuebleNoEncontrado(f"Inmueble {inmueble_id} no existe")

    await _autorizar_publicador_sobre_inmueble(
        current_publicador,
        inmueble.propietario_id,
        relacion_repository=relacion_repository,
        usuario_repository=usuario_repository,
    )

    command = EditarInmuebleCommand(
        inmueble_id=inmueble_id,
        propietario_id=inmueble.propietario_id,
        direccion=payload.direccion,
        barrio=payload.barrio,
        ciudad=payload.ciudad,
        tipo=payload.tipo,
        area_m2=payload.area_m2,
        habitaciones=payload.habitaciones,
        banos=payload.banos,
        valor_mensual=payload.valor_mensual,
        descripcion=payload.descripcion,
    )

    inmueble = await editar_inmueble(command, repository=repository)
    return InmuebleResponse.from_domain(inmueble)


@router.patch("/{inmueble_id}/disponibilidad", response_model=InmuebleResponse)
async def cambiar_disponibilidad_endpoint(
    inmueble_id: uuid.UUID,
    payload: CambiarDisponibilidadRequest,
    current_publicador: CurrentPublicador,
    repository: Repository,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> InmuebleResponse:
    """`PATCH /inmuebles/{inmueble_id}/disponibilidad` — despublicar
    (`"oculto"`) or republicar (`"disponible"`) a listing.

    Same ownership/agente authorization semantics as `PUT` (403/404)."""
    inmueble = await repository.obtener_por_id(inmueble_id)
    if inmueble is None:
        raise InmuebleNoEncontrado(f"Inmueble {inmueble_id} no existe")

    await _autorizar_publicador_sobre_inmueble(
        current_publicador,
        inmueble.propietario_id,
        relacion_repository=relacion_repository,
        usuario_repository=usuario_repository,
    )

    command = CambiarDisponibilidadCommand(
        inmueble_id=inmueble_id,
        nuevo_estado=EstadoInmueble(payload.nuevo_estado),
        propietario_id=inmueble.propietario_id,
    )

    inmueble = await cambiar_disponibilidad(command, repository=repository)
    return InmuebleResponse.from_domain(inmueble)


@router.get("/mios", response_model=list[InmuebleResponse])
async def listar_mis_inmuebles_endpoint(
    current_propietario: CurrentPropietario,
    repository: Repository,
) -> list[InmuebleResponse]:
    """`GET /inmuebles/mios` — every listing owned by the authenticated
    propietario (empty list when there are none)."""
    command = ListarMisInmueblesCommand(propietario_id=uuid.UUID(current_propietario.sub))
    inmuebles = await listar_mis_inmuebles(command, repository=repository)
    return [InmuebleResponse.from_domain(inmueble) for inmueble in inmuebles]


@router.get("/gestionados", response_model=list[InmuebleResponse])
async def listar_inmuebles_gestionados_endpoint(
    current_agente: CurrentAgente,
    repository: Repository,
    relacion_repository: RelacionRepository,
    usuario_repository: UsuarioAgenciaRepository,
) -> list[InmuebleResponse]:
    """`GET /inmuebles/gestionados` (hu-002) — every listing owned by any
    propietario with an `ACTIVA` relación with the authenticated agente's
    agencia (empty list when the agente belongs to no agencia, or their
    agencia manages none)."""
    agencia_id = await usuario_repository.obtener_agencia_id(uuid.UUID(current_agente.sub))
    propietario_ids: list[uuid.UUID] = []
    if agencia_id is not None:
        relaciones = await relacion_repository.listar_por_agencia(agencia_id)
        propietario_ids = [
            relacion.propietario_id
            for relacion in relaciones
            if relacion.estado == EstadoRelacion.ACTIVA
        ]

    inmuebles = await listar_inmuebles_gestionados(propietario_ids, repository=repository)
    return [InmuebleResponse.from_domain(inmueble) for inmueble in inmuebles]
