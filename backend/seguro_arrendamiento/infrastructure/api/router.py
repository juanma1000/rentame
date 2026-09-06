"""HTTP API for the `seguro-arrendamiento` domain (task 5.3 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`).

`POST /seguro-arrendamiento/contratar` only orchestrates: it reads the
multipart request (cédula + support documents), maps it into
`ContratarSeguroArrendamientoCommand`, calls the use case (real
Postgres-backed repositories, injected via `Depends`), and maps the
resulting domain entity to `ContratarSeguroArrendamientoResponse`. No
business rule is re-implemented at this layer — same precedent as
`identidad/infrastructure/api/router.py`.

Per spec.md's "Documentación de soporte no se persiste", the raw bytes read
here (`await documento.read()` for each uploaded file) are only ever
passed to `contratar_seguro_arrendamiento`, which forwards them to the
injected `proveedor` and never stores them — this router does not write
them to disk/object storage either.

`seguro_arrendamiento.domain.exceptions.IdentidadNoVerificada` is not
caught here — it propagates to the app-level exception handler registered
in `main.py`, mapped to `403` with a `{"detail": "<message>"}` body, same
convention as every other domain exception handler.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from seguro_arrendamiento.application.consultar_estado_seguro import consultar_estado_seguro
from seguro_arrendamiento.application.contratar_seguro_arrendamiento import (
    ContratarSeguroArrendamientoCommand,
    contratar_seguro_arrendamiento,
)
from seguro_arrendamiento.domain.ports import ProveedorSeguroArrendamientoPort
from seguro_arrendamiento.infrastructure.api.schemas import (
    ContratarSeguroArrendamientoResponse,
    EstadoSeguroResponse,
)
from seguro_arrendamiento.infrastructure.persistence.repository import (
    PolizaArrendamientoRepositoryPostgres,
    UsuarioIdentidadRepositoryPostgres,
)
from seguro_arrendamiento.infrastructure.proveedor import get_proveedor_seguro_arrendamiento
from shared.infrastructure.auth.dependencies import get_current_inquilino
from shared.infrastructure.auth.jwt_handler import TokenPayload
from shared.infrastructure.database import get_db_session

router = APIRouter(prefix="/seguro-arrendamiento", tags=["seguro-arrendamiento"])


def get_poliza_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PolizaArrendamientoRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return PolizaArrendamientoRepositoryPostgres(session)


def get_usuario_identidad_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsuarioIdentidadRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return UsuarioIdentidadRepositoryPostgres(session)


CurrentInquilino = Annotated[TokenPayload, Depends(get_current_inquilino)]
PolizaRepository = Annotated[
    PolizaArrendamientoRepositoryPostgres, Depends(get_poliza_repository)
]
UsuarioIdentidadRepository = Annotated[
    UsuarioIdentidadRepositoryPostgres, Depends(get_usuario_identidad_repository)
]
Proveedor = Annotated[
    ProveedorSeguroArrendamientoPort, Depends(get_proveedor_seguro_arrendamiento)
]


@router.post(
    "/contratar",
    status_code=status.HTTP_200_OK,
    response_model=ContratarSeguroArrendamientoResponse,
)
async def contratar_seguro_arrendamiento_endpoint(
    current_inquilino: CurrentInquilino,
    poliza_repository: PolizaRepository,
    usuario_identidad_repository: UsuarioIdentidadRepository,
    proveedor: Proveedor,
    cedula: Annotated[str, Form()],
    documentos: Annotated[list[UploadFile], File()],
) -> ContratarSeguroArrendamientoResponse:
    """`POST /seguro-arrendamiento/contratar` — an inquilino submits their
    cédula plus the support documents (desprendibles de pago, certificado
    laboral), proxied straight to `proveedor` (`FakeAdapter` by default,
    `SuraAdapter` in prod per task 6.3).

    Rejects (`IdentidadNoVerificada` -> `403`, mapped in `main.py`) when the
    account does not have `identidad_verificada = True` — no document is
    ever read in that case's earlier check
    (`usuario_identidad_repository.esta_verificado`), but FastAPI still
    enforces the multipart fields' presence for every request (missing
    `cedula`/`documentos` -> `422`).
    """
    documentos_bytes = [await documento.read() for documento in documentos]

    command = ContratarSeguroArrendamientoCommand(
        usuario_id=uuid.UUID(current_inquilino.sub),
        cedula=cedula,
        documentos=documentos_bytes,
    )
    poliza = await contratar_seguro_arrendamiento(
        command,
        poliza_repository=poliza_repository,
        usuario_identidad=usuario_identidad_repository,
        proveedor=proveedor,
    )
    return ContratarSeguroArrendamientoResponse.from_domain(poliza)


@router.get("/estado", status_code=status.HTTP_200_OK, response_model=EstadoSeguroResponse)
async def consultar_estado_seguro_endpoint(
    current_inquilino: CurrentInquilino,
    poliza_repository: PolizaRepository,
) -> EstadoSeguroResponse:
    """`GET /seguro-arrendamiento/estado` — read-only: returns the current
    inquilino's seguro de arrendamiento estado (`"no_iniciado"` if no
    `PolizaArrendamiento` exists, otherwise the most recent one's estado
    and `prima_mensual`), so the `frontend-flujo-arrendamiento` wizard can
    know which step it is on without depending on error codes from
    `POST /seguro-arrendamiento/contratar`.

    Never creates or modifies any record, and never calls `proveedor` —
    same rationale as `consultar_estado_seguro`'s own docstring.
    """
    resultado = await consultar_estado_seguro(
        uuid.UUID(current_inquilino.sub),
        poliza_repository=poliza_repository,
    )
    return EstadoSeguroResponse(estado=resultado.estado, prima_mensual=resultado.prima_mensual)
