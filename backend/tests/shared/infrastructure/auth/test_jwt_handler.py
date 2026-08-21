"""Unit tests for shared/infrastructure/auth/jwt_handler.py.

No database or network access required — pure token issuance/validation.
"""

from datetime import timedelta
from uuid import uuid4

import pytest

from shared.infrastructure.auth.jwt_handler import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)


class TestCreateAndDecodeAccessToken:
    def test_should_return_original_claims_when_token_is_valid(self) -> None:
        # Arrange
        usuario_id = str(uuid4())
        rol = "propietario"

        # Act
        token = create_access_token(usuario_id=usuario_id, rol=rol)
        payload = decode_access_token(token)

        # Assert
        assert payload.sub == usuario_id
        assert payload.rol == rol

    def test_should_produce_a_non_empty_string_token(self) -> None:
        # Arrange / Act
        token = create_access_token(usuario_id=str(uuid4()), rol="propietario")

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0


class TestDecodeAccessTokenInvalidCases:
    def test_should_raise_invalid_token_error_when_token_is_malformed(self) -> None:
        # Arrange
        malformed_token = "not-a-valid-jwt"

        # Act / Assert
        with pytest.raises(InvalidTokenError):
            decode_access_token(malformed_token)

    def test_should_raise_invalid_token_error_when_signature_does_not_match(self) -> None:
        # Arrange: a syntactically valid JWT signed with a different secret.
        from jose import jwt as jose_jwt

        tampered_token = jose_jwt.encode(
            {"sub": str(uuid4()), "rol": "propietario"},
            "a-completely-different-secret",
            algorithm="HS256",
        )

        # Act / Assert
        with pytest.raises(InvalidTokenError):
            decode_access_token(tampered_token)

    def test_should_raise_invalid_token_error_when_token_is_expired(self) -> None:
        # Arrange: issue a token that expired one minute ago.
        token = create_access_token(
            usuario_id=str(uuid4()),
            rol="propietario",
            expires_delta=timedelta(minutes=-1),
        )

        # Act / Assert
        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_should_raise_invalid_token_error_when_required_claim_is_missing(self) -> None:
        # Arrange: a valid signature, but missing the "rol" claim.
        from jose import jwt as jose_jwt

        from shared.infrastructure.settings import get_settings

        settings = get_settings()
        token_without_rol = jose_jwt.encode(
            {"sub": str(uuid4())},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        # Act / Assert
        with pytest.raises(InvalidTokenError):
            decode_access_token(token_without_rol)
