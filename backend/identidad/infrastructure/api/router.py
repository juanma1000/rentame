"""HTTP API for the `identidad` domain (task 5.3 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`).

`POST /identidad/validar` only orchestrates: it reads the multipart
request (cédula + document images), maps it into
`IniciarValidacionIdentidadCommand`, calls the use case (real
Postgres-backed repositories, injected via `Depends`), and maps the
resulting domain entity to `ValidarIdentidadResponse`. No business rule is
re-implemented at this layer — same precedent as
`agencias/infrastructure/api/router.py`.

Per spec.md's "Imágenes del documento no se persisten", the raw bytes read
here (`await imagen_frente.read()`) are only ever passed to
`iniciar_validacion_identidad`, which forwards them to the injected
`proveedor` and never stores them — this router does not write them to
disk/object storage either, unlike `inmuebles`' photo upload endpoint.

`identidad.domain.exceptions.IdentidadYaVerificada` is not caught here — it
propagates to the app-level exception handler registered in `main.py`,
mapped to `409` with a `{"detail": "<message>"}` body, same convention as
every other domain exception handler.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from identidad.application.iniciar_validacion_identidad import (
    IniciarValidacionIdentidadCommand,
    iniciar_validacion_identidad,
)
from identidad.domain.ports import ProveedorValidacionIdentidadPort
from identidad.infrastructure.api.schemas import ValidarIdentidadResponse
from identidad.infrastructure.persistence.repository import (
    UsuarioIdentidadRepositoryPostgres,
    ValidacionIdentidadRepositoryPostgres,
)
from identidad.infrastructure.proveedor import get_proveedor_validacion_identidad
from shared.infrastructure.auth.dependencies import get_current_inquilino
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session

router = APIRouter(prefix="/identidad", tags=["identidad"])


def get_validacion_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ValidacionIdentidadRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return ValidacionIdentidadRepositoryPostgres(session)


def get_usuario_identidad_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsuarioIdentidadRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return UsuarioIdentidadRepositoryPostgres(session)


CurrentInquilino = Annotated[TokenPayload, Depends(get_current_inquilino)]
ValidacionRepository = Annotated[
    ValidacionIdentidadRepositoryPostgres, Depends(get_validacion_repository)
]
UsuarioIdentidadRepository = Annotated[
    UsuarioIdentidadRepositoryPostgres, Depends(get_usuario_identidad_repository)
]
Proveedor = Annotated[
    ProveedorValidacionIdentidadPort, Depends(get_proveedor_validacion_identidad)
]


@router.post("/validar", status_code=status.HTTP_200_OK, response_model=ValidarIdentidadResponse)
async def validar_identidad_endpoint(
    current_inquilino: CurrentInquilino,
    validacion_repository: ValidacionRepository,
    usuario_repository: UsuarioIdentidadRepository,
    proveedor: Proveedor,
    cedula: Annotated[str, Form()],
    imagen_frente: Annotated[UploadFile, File()],
    imagen_dorso: Annotated[UploadFile, File()],
) -> ValidarIdentidadResponse:
    """`POST /identidad/validar` — an inquilino submits their cédula plus
    the document's front/back images, proxied straight to `proveedor`
    (`FakeAdapter` by default, `TruoraAdapter` in prod per task 6.3).

    Rejects (`IdentidadYaVerificada` -> `409`, mapped in `main.py`) when the
    account already has an approved validación — no image is ever read in
    that case's earlier check (`usuario_repository.esta_verificado`), but
    FastAPI still enforces the multipart fields' presence for every request
    (missing `cedula`/`imagen_frente`/`imagen_dorso` -> `422`).
    """
    frente_bytes = await imagen_frente.read()
    dorso_bytes = await imagen_dorso.read()

    command = IniciarValidacionIdentidadCommand(
        usuario_id=uuid.UUID(current_inquilino.sub),
        cedula=cedula,
        imagen_frente=frente_bytes,
        imagen_dorso=dorso_bytes,
    )
    validacion = await iniciar_validacion_identidad(
        command,
        validacion_repository=validacion_repository,
        usuario_repository=usuario_repository,
        proveedor=proveedor,
    )
    return ValidarIdentidadResponse.from_domain(validacion)
