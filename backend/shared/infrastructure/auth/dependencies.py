"""FastAPI authentication/authorization dependencies.

`get_current_propietario` is consumed by `inmuebles` endpoints (a later
phase) to enforce that only authenticated users with role "propietario" can
create/edit/list their properties. It is implemented and tested here ahead
of that phase since it is transversal, shared infrastructure.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.infrastructure.auth.jwt_handler import (
    InvalidTokenError,
    TokenPayload,
    decode_access_token,
)

ROL_PROPIETARIO = "propietario"
ROL_AGENTE = "agente"
ROLES_PUBLICADOR = (ROL_PROPIETARIO, ROL_AGENTE)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_propietario(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header.

    Raises 401 when the token is missing, invalid/expired, or belongs to a
    user whose role is not "propietario".
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    if payload.rol != ROL_PROPIETARIO:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User role is not authorized to perform this operation",
        )

    return payload


async def get_current_agente(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header.

    Raises 401 when the token is missing, invalid/expired, or belongs to a
    user whose role is not "agente".
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    if payload.rol != ROL_AGENTE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User role is not authorized to perform this operation",
        )

    return payload


async def get_current_publicador(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header.

    Raises 401 when the token is missing, invalid/expired, or belongs to a
    user whose role is neither "propietario" nor "agente" (hu-002,
    design.md decisión 2: the router needs both identity and role to decide
    the publishing flow).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    if payload.rol not in ROLES_PUBLICADOR:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User role is not authorized to perform this operation",
        )

    return payload
