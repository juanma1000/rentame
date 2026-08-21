"""HTTP API for the `inmuebles` domain (tasks 7.3-7.6 of
`openspec/changes/hu-001/tasks.md`).

Every endpoint requires an authenticated "propietario" (`get_current_
propietario`, reused as-is from `shared/infrastructure/auth/dependencies.py`
— not reimplemented here) and only orchestrates: it maps the HTTP
request/JWT into the corresponding use case's command, calls the use case,
and maps the resulting `Inmueble` (or list of them) to `InmuebleResponse`.
No business rule is re-implemented at this layer.

Domain exceptions (`DomainValidationError`, `InmuebleNoEncontrado`,
`PropietarioInvalido`) are not caught here — they propagate to the
app-level exception handlers registered in `main.py`, which map them to
422/404/403 respectively with a `{"detail": "<message>"}` body, per the
contract fixed by `tests/inmuebles/infrastructure/test_api.py`.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from inmuebles.application.cambiar_disponibilidad import (
    CambiarDisponibilidadCommand,
    cambiar_disponibilidad,
)
from inmuebles.application.editar_inmueble import EditarInmuebleCommand, editar_inmueble
from inmuebles.application.listar_mis_inmuebles import (
    ListarMisInmueblesCommand,
    listar_mis_inmuebles,
)
from inmuebles.application.publicar_inmueble import (
    FotoParaPublicar,
    PublicarInmuebleCommand,
    publicar_inmueble,
)
from inmuebles.domain.inmueble import EstadoInmueble
from inmuebles.infrastructure.api.schemas import (
    CambiarDisponibilidadRequest,
    InmuebleEditRequest,
    InmuebleResponse,
)
from inmuebles.infrastructure.external.s3_storage_adapter import S3StorageAdapter
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from shared.infrastructure.auth.dependencies import get_current_propietario
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


CurrentPropietario = Annotated[TokenPayload, Depends(get_current_propietario)]
Repository = Annotated[InmuebleRepositoryPostgres, Depends(get_inmueble_repository)]
Storage = Annotated[S3StorageAdapter, Depends(get_storage_adapter)]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=InmuebleResponse)
async def crear_inmueble(
    current_propietario: CurrentPropietario,
    repository: Repository,
    storage: Storage,
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
) -> InmuebleResponse:
    """`POST /inmuebles/` — create a listing with 1 to `MAX_FOTOS_INMUEBLE`
    photos, starting in `EstadoInmueble.DISPONIBLE`."""
    fotos_para_publicar = [
        FotoParaPublicar(contenido=await foto.read(), es_principal=(indice == 0))
        for indice, foto in enumerate(fotos)
    ]

    command = PublicarInmuebleCommand(
        propietario_id=uuid.UUID(current_propietario.sub),
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
    )

    inmueble = await publicar_inmueble(command, repository=repository, storage=storage)
    return InmuebleResponse.from_domain(inmueble)


@router.put("/{inmueble_id}", response_model=InmuebleResponse)
async def editar_inmueble_endpoint(
    inmueble_id: uuid.UUID,
    payload: InmuebleEditRequest,
    current_propietario: CurrentPropietario,
    repository: Repository,
) -> InmuebleResponse:
    """`PUT /inmuebles/{inmueble_id}` — edit an owned listing's data.

    Only succeeds when the JWT's `sub` matches the listing's
    `propietario_id` (`PropietarioInvalido` -> 403 otherwise,
    `InmuebleNoEncontrado` -> 404 when it does not exist)."""
    command = EditarInmuebleCommand(
        inmueble_id=inmueble_id,
        propietario_id=uuid.UUID(current_propietario.sub),
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
    current_propietario: CurrentPropietario,
    repository: Repository,
) -> InmuebleResponse:
    """`PATCH /inmuebles/{inmueble_id}/disponibilidad` — despublicar
    (`"oculto"`) or republicar (`"disponible"`) an owned listing.

    Same ownership semantics as `PUT` (403/404)."""
    command = CambiarDisponibilidadCommand(
        inmueble_id=inmueble_id,
        nuevo_estado=EstadoInmueble(payload.nuevo_estado),
        propietario_id=uuid.UUID(current_propietario.sub),
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
