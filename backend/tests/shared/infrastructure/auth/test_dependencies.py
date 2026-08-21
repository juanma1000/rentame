"""Unit tests for shared/infrastructure/auth/dependencies.py.

`get_current_propietario` is exercised directly as an async function (not
through a full FastAPI app + TestClient) since it has no other collaborators
besides the JWT it receives.
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from shared.infrastructure.auth.dependencies import get_current_propietario
from shared.infrastructure.auth.jwt_handler import create_access_token


def _credentials_for(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestGetCurrentPropietarioValidToken:
    async def test_should_return_payload_when_token_has_propietario_role(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        token = create_access_token(usuario_id=usuario_id, rol="propietario")

        # Act
        payload = await get_current_propietario(_credentials_for(token))

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == "propietario"


class TestGetCurrentPropietarioRejectedCases:
    async def test_should_raise_401_when_authorization_header_is_missing(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_propietario(None)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_token_is_invalid(self) -> None:
        # Arrange
        credentials = _credentials_for("not-a-valid-jwt")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_propietario(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_not_propietario(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="inquilino")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_propietario(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_agente(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="agente")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_propietario(credentials)

        assert exc_info.value.status_code == 401
