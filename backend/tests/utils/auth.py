"""Test helper for issuing JWTs, reused by integration tests of later phases
(e.g. `inmuebles` endpoint tests) to authenticate as a given user/role.
"""

from shared.infrastructure.auth.jwt_handler import create_access_token


def build_valid_token(usuario_id: str, rol: str) -> str:
    """Issue a valid JWT for the given user id and role, for use in tests."""
    return create_access_token(usuario_id=usuario_id, rol=rol)
