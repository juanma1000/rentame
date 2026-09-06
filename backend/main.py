"""FastAPI application entrypoint.

Registers routers and middleware. Contains no business logic — routers live
in each domain's `infrastructure/api/router.py` (added as domains land).

Domain exceptions raised by use cases (`inmuebles.domain.exceptions`,
`shared.domain.exceptions`) are mapped here, once, to HTTP responses via
`@app.exception_handler(...)` (per `docs/backend-standards.md`'s "Manejo de
Errores" pattern), instead of duplicating try/except blocks in every
endpoint. The `{"detail": "<message>"}` body shape matches the contract
fixed by `tests/inmuebles/infrastructure/test_api.py`.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agencias.domain.exceptions import (
    AgenteNoEsMiembroDeAgencia,
    AgenteYaTieneAgencia,
    RelacionNoEncontrada,
    SolicitudNoEncontrada,
    UltimoAgenteConRelacionesActivas,
)
from agencias.domain.exceptions import PropietarioInvalido as AgenciaPropietarioInvalido
from agencias.infrastructure.api.router import router as agencias_router
from identidad.domain.exceptions import IdentidadYaVerificada, ValidacionNoDisponible
from identidad.infrastructure.api.router import router as identidad_router
from inmuebles.domain.exceptions import InmuebleNoEncontrado, PropietarioInvalido
from inmuebles.infrastructure.api.router import router as inmuebles_router
from seguro_arrendamiento.domain.exceptions import ContratacionNoDisponible, IdentidadNoVerificada
from seguro_arrendamiento.infrastructure.api.router import router as seguro_arrendamiento_router
from shared.domain.exceptions import DomainValidationError
from shared.infrastructure.settings import get_settings
from usuarios.domain.exceptions import CredencialesInvalidas, EmailYaRegistrado
from usuarios.infrastructure.api.router import router as usuarios_router

# `UsuarioORM` is never referenced directly by the API layer here, but
# importing it (transitively, via `usuarios_router`'s own imports) is
# required so it registers on `Base.metadata` before any request touches the
# database: `InmuebleORM.propietario_id`/`agente_id` declare
# `ForeignKey("usuario.id")`, and SQLAlchemy raises `NoReferencedTableError`
# on the first INSERT/flush if that mapper was never configured in this
# process. `alembic/env.py` needs the same import for the same reason — add
# new domains' models here as they land.
from usuarios.infrastructure.persistence.models import UsuarioORM  # noqa: F401

settings = get_settings()

app = FastAPI(title=settings.app_name)

# Frontend microfrontends (shell :3000, remotes like inmuebles-app :3001) run
# on different origins than the API in local dev. Without this, every
# fetch from the browser fails the CORS preflight before reaching a route.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inmuebles_router)
app.include_router(agencias_router)
app.include_router(usuarios_router)
app.include_router(identidad_router)
app.include_router(seguro_arrendamiento_router)


@app.exception_handler(DomainValidationError)
async def domain_validation_error_handler(
    request: Request, exc: DomainValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InmuebleNoEncontrado)
async def inmueble_no_encontrado_handler(
    request: Request, exc: InmuebleNoEncontrado
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PropietarioInvalido)
async def propietario_invalido_handler(request: Request, exc: PropietarioInvalido) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(AgenciaPropietarioInvalido)
async def agencia_propietario_invalido_handler(
    request: Request, exc: AgenciaPropietarioInvalido
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(AgenteYaTieneAgencia)
async def agente_ya_tiene_agencia_handler(
    request: Request, exc: AgenteYaTieneAgencia
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(SolicitudNoEncontrada)
async def solicitud_no_encontrada_handler(
    request: Request, exc: SolicitudNoEncontrada
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RelacionNoEncontrada)
async def relacion_no_encontrada_handler(
    request: Request, exc: RelacionNoEncontrada
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(AgenteNoEsMiembroDeAgencia)
async def agente_no_es_miembro_de_agencia_handler(
    request: Request, exc: AgenteNoEsMiembroDeAgencia
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(UltimoAgenteConRelacionesActivas)
async def ultimo_agente_con_relaciones_activas_handler(
    request: Request, exc: UltimoAgenteConRelacionesActivas
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(EmailYaRegistrado)
async def email_ya_registrado_handler(request: Request, exc: EmailYaRegistrado) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(CredencialesInvalidas)
async def credenciales_invalidas_handler(
    request: Request, exc: CredencialesInvalidas
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(IdentidadYaVerificada)
async def identidad_ya_verificada_handler(
    request: Request, exc: IdentidadYaVerificada
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidacionNoDisponible)
async def validacion_no_disponible_handler(
    request: Request, exc: ValidacionNoDisponible
) -> JSONResponse:
    """The proveedor externo (Truora) could not be reached — a clear,
    non-500 response per design.md's risk mitigation, so the inquilino sees
    an explicit "reintentar" state instead of a generic server error."""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(IdentidadNoVerificada)
async def identidad_no_verificada_handler(
    request: Request, exc: IdentidadNoVerificada
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ContratacionNoDisponible)
async def contratacion_no_disponible_handler(
    request: Request, exc: ContratacionNoDisponible
) -> JSONResponse:
    """The proveedor externo (Sura) could not be reached — a clear, non-500
    response per design.md's risk mitigation, so the inquilino sees an
    explicit "reintentar" state instead of a generic server error."""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness/readiness probe used by deployment tooling and local checks."""
    return {"status": "ok"}
