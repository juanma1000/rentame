"""Unit tests for shared/infrastructure/auth/dependencies.py.

`get_current_propietario` is exercised directly as an async function (not
through a full FastAPI app + TestClient) since it has no other collaborators
besides the JWT it receives.
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from shared.infrastructure.auth.dependencies import (
    get_current_agente,
    get_current_inquilino,
    get_current_propietario,
    get_current_publicador,
)
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


class TestGetCurrentAgenteValidToken:
    async def test_should_return_payload_when_token_has_agente_role(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        token = create_access_token(usuario_id=usuario_id, rol="agente")

        # Act
        payload = await get_current_agente(_credentials_for(token))

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == "agente"


class TestGetCurrentAgenteRejectedCases:
    async def test_should_raise_401_when_authorization_header_is_missing(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_agente(None)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_token_is_invalid(self) -> None:
        # Arrange
        credentials = _credentials_for("not-a-valid-jwt")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_agente(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_not_agente(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="propietario")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_agente(credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentInquilinoValidToken:
    """`get_current_inquilino`, added by
    `openspec/changes/validacion-identidad-inquilino` (task 5.x): the
    `POST /identidad/validar` endpoint needs an authenticated inquilino,
    same shape as `get_current_propietario`/`get_current_agente`."""

    async def test_should_return_payload_when_token_has_inquilino_role(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        token = create_access_token(usuario_id=usuario_id, rol="inquilino")

        # Act
        payload = await get_current_inquilino(_credentials_for(token))

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == "inquilino"


class TestGetCurrentInquilinoRejectedCases:
    async def test_should_raise_401_when_authorization_header_is_missing(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_inquilino(None)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_token_is_invalid(self) -> None:
        # Arrange
        credentials = _credentials_for("not-a-valid-jwt")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_inquilino(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_not_inquilino(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="propietario")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_inquilino(credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentPublicadorValidToken:
    """`get_current_publicador` (hu-002, design.md decisión 2) accepts a JWT
    with role "propietario" OR "agente" and returns their identity + role,
    since the router needs both to decide the publishing flow (Decisión 2:
    propietario uses their own id; agente must supply `propietario_id` and
    have it authorized against `agencias`).

    Contract fixed here: returns the same `TokenPayload` shape already used
    by `get_current_propietario`/`get_current_agente` (`.sub` = usuario_id,
    `.rol` = "propietario" | "agente") — no new type is introduced.
    """

    async def test_should_return_payload_when_token_has_propietario_role(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        token = create_access_token(usuario_id=usuario_id, rol="propietario")

        # Act
        payload = await get_current_publicador(_credentials_for(token))

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == "propietario"

    async def test_should_return_payload_when_token_has_agente_role(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        token = create_access_token(usuario_id=usuario_id, rol="agente")

        # Act
        payload = await get_current_publicador(_credentials_for(token))

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == "agente"


class TestGetCurrentPublicadorRejectedCases:
    async def test_should_raise_401_when_authorization_header_is_missing(self) -> None:
        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_publicador(None)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_token_is_invalid(self) -> None:
        # Arrange
        credentials = _credentials_for("not-a-valid-jwt")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_publicador(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_token_is_expired(self) -> None:
        # Arrange
        from datetime import timedelta

        token = create_access_token(
            usuario_id=str(uuid4()),
            rol="propietario",
            expires_delta=timedelta(minutes=-1),
        )
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_publicador(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_inquilino(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="inquilino")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_publicador(credentials)

        assert exc_info.value.status_code == 401

    async def test_should_raise_401_when_role_is_any_other_unrecognized_value(self) -> None:
        # Arrange
        token = create_access_token(usuario_id=str(uuid4()), rol="administrador")
        credentials = _credentials_for(token)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_publicador(credentials)

        assert exc_info.value.status_code == 401
