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

from inmuebles.domain.exceptions import InmuebleNoEncontrado, PropietarioInvalido
from inmuebles.infrastructure.api.router import router as inmuebles_router
from shared.domain.exceptions import DomainValidationError
from shared.infrastructure.settings import get_settings

# `UsuarioORM` is never referenced directly by the API layer (no `usuarios`
# router yet), but importing it here is required so it registers on
# `Base.metadata` before any request touches the database: `InmuebleORM.
# propietario_id`/`agente_id` declare `ForeignKey("usuario.id")`, and
# SQLAlchemy raises `NoReferencedTableError` on the first INSERT/flush if
# that mapper was never configured in this process. `alembic/env.py` needs
# the same import for the same reason — add new domains' models here as
# they land.
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness/readiness probe used by deployment tooling and local checks."""
    return {"status": "ok"}
