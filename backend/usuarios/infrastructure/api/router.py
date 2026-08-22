"""HTTP API for the `usuarios` domain (tasks 4.2/4.4/4.5 of
`openspec/changes/hu-008/tasks.md`).

Every endpoint only orchestrates: it maps the HTTP request body into the
corresponding use case's command, calls the use case (real Postgres-backed
repository, injected via `Depends`), and maps the resulting domain entity to
`AuthResponse`. No business rule is re-implemented at this layer — same
precedent as `agencias/infrastructure/api/router.py`.

Domain exceptions (`EmailYaRegistrado`, `CredencialesInvalidas`) are not
caught here — they propagate to the app-level exception handlers registered
in `main.py`, which map them to 409/401 respectively with a
`{"detail": "<message>"}` body, per the contract fixed by
`tests/usuarios/infrastructure/test_api.py`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.infrastructure.auth.jwt_handler import create_access_token
from shared.infrastructure.database import get_db_session
from usuarios.application.autenticar_usuario import AutenticarUsuarioCommand, autenticar_usuario
from usuarios.application.registrar_usuario import RegistrarUsuarioCommand, registrar_usuario
from usuarios.infrastructure.api.schemas import (
    AuthResponse,
    LoginRequest,
    RegistroRequest,
    UsuarioResponse,
)
from usuarios.infrastructure.persistence.repository import UsuarioRepositoryPostgres

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def get_usuario_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsuarioRepositoryPostgres:
    """Build a repository bound to the request-scoped `AsyncSession`."""
    return UsuarioRepositoryPostgres(session)


UsuarioRepository = Annotated[UsuarioRepositoryPostgres, Depends(get_usuario_repository)]


@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def registro_endpoint(
    payload: RegistroRequest,
    usuario_repository: UsuarioRepository,
) -> AuthResponse:
    """`POST /usuarios/registro` — create a new `Usuario` account and issue a
    JWT for it. Rejects (`EmailYaRegistrado` -> 409) when `payload.email`
    already has an account associated."""
    command = RegistrarUsuarioCommand(
        email=payload.email,
        password=payload.password,
        nombre=payload.nombre,
        rol=payload.rol,
    )
    usuario = await registrar_usuario(command, usuario_repository=usuario_repository)
    assert usuario.id is not None
    access_token = create_access_token(str(usuario.id), usuario.rol)
    return AuthResponse(access_token=access_token, usuario=UsuarioResponse.from_domain(usuario))


@router.post("/login", response_model=AuthResponse)
async def login_endpoint(
    payload: LoginRequest,
    usuario_repository: UsuarioRepository,
) -> AuthResponse:
    """`POST /usuarios/login` — authenticate by email/password and issue a
    JWT. Rejects (`CredencialesInvalidas` -> 401) both when the email does
    not exist and when the password does not match, with the same message
    in both cases."""
    command = AutenticarUsuarioCommand(email=payload.email, password=payload.password)
    usuario = await autenticar_usuario(command, usuario_repository=usuario_repository)
    assert usuario.id is not None
    access_token = create_access_token(str(usuario.id), usuario.rol)
    return AuthResponse(access_token=access_token, usuario=UsuarioResponse.from_domain(usuario))
