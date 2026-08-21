"""JWT issuance and validation.

Tokens carry two claims relevant to authorization: `sub` (the issuing
user's id) and `rol` (their role — "propietario" | "agente" | "inquilino").
`get_current_propietario` (see `dependencies.py`) relies on both.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from shared.infrastructure.settings import get_settings


class TokenPayload(BaseModel):
    """Claims extracted from a validated JWT."""

    sub: str
    rol: str


class InvalidTokenError(Exception):
    """Raised when a token is malformed, has an invalid signature, is expired,
    or is missing a required claim.
    """


def create_access_token(usuario_id: str, rol: str, expires_delta: timedelta | None = None) -> str:
    """Issue a signed JWT for the given user id and role."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
    )
    claims: dict[str, str | datetime] = {"sub": usuario_id, "rol": rol, "exp": expire}
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Validate and decode a JWT, returning its claims.

    Raises `InvalidTokenError` for any failure: bad signature, expired token,
    malformed token, or missing required claims.
    """
    settings = get_settings()
    try:
        raw_payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as error:
        raise InvalidTokenError("Invalid or expired token") from error

    sub = raw_payload.get("sub")
    rol = raw_payload.get("rol")
    if sub is None or rol is None:
        raise InvalidTokenError("Token payload is missing required claims (sub, rol)")

    return TokenPayload(sub=sub, rol=rol)
