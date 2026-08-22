"""Integration tests for the `usuarios` API layer (tasks 4.1 and 4.3 of
`openspec/changes/hu-008/tasks.md`), covering every scenario of
`openspec/changes/hu-008/specs/usuarios/spec.md` relevant to registro/login,
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`) and a real PostgreSQL test database (`rentame_test`, via
`db_session` from `backend/tests/conftest.py`) — no mocks anywhere,
following the precedent of `tests/agencias/infrastructure/test_api.py`.

TDD Red phase: neither `POST /usuarios/registro` nor `POST /usuarios/login`
exist yet — `main.py` registers no router for the `usuarios` domain, and
neither `usuarios/infrastructure/api/router.py` nor
`usuarios/infrastructure/api/schemas.py` exist. Every request below is
therefore expected to fail with FastAPI's default 404 (no matching route)
today, not with an import/collection error, since this file only imports
`main.app` plus already-existing collaborators (the domain entities, the
real Postgres-backed repository once it exists per task 3.3, and
`shared.infrastructure.auth.jwt_handler.decode_access_token`). This file
fixes, by construction, the exact contract `backend-expert` must implement:

- `POST /usuarios/registro` — JSON body
  `{"email": str, "password": str, "nombre": str, "rol": "propietario" |
  "agente" | "inquilino"}`. No authentication required. `201` on success,
  with body:
  ```
  {
    "access_token": "<jwt>",
    "usuario": {
      "id": "<uuid>",
      "email": str,
      "nombre": str,
      "rol": "propietario" | "agente" | "inquilino"
    }
  }
  ```
  `access_token` must decode via `jwt_handler.decode_access_token` to a
  payload whose `sub` equals `usuario.id` and whose `rol` equals
  `usuario.rol`. `password`/`password_hash` MUST NOT appear anywhere in the
  response body. Missing any required field (e.g. `email`) -> `422`
  (FastAPI's own body validation). Email already registered -> `409`
  (domain `EmailYaRegistrado`, chosen for consistency with the existing
  `AgenteYaTieneAgencia` -> 409 mapping in `main.py` — both are "this
  resource/identity already exists" conflicts) with body
  `{"detail": "<message>"}`; no new row must be created in `usuario`.

- `POST /usuarios/login` — JSON body `{"email": str, "password": str}`. No
  authentication required. `200` on success, same response body shape as
  registro above (`access_token` + `usuario`). Login rejected — email does
  not exist OR password does not match — MUST return the exact same status
  code and the exact same response body (`401`, `{"detail": "<message>"}`,
  same `<message>` text) in both cases, per spec.md "Login rechazado sin
  revelar cuál dato falló" and design.md decisión 5 (`CredencialesInvalidas`
  mapped once, in `main.py`, to `401`). This file asserts that equivalence
  directly, not just that both cases are individually rejected.

Every test that persists a `Usuario` relies on `db_session`'s per-test
rollback (see `backend/tests/conftest.py`) for Postgres cleanup — the
`client` fixture below overrides `get_db_session` with that same session
instance so every request in a test shares one transaction, exactly like
`tests/agencias/infrastructure/test_api.py` already does.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from shared.infrastructure.auth.jwt_handler import decode_access_token
from shared.infrastructure.database import get_db_session

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """`httpx.AsyncClient` bound to the real `main.app`, with `get_db_session`
    overridden so every request in a test reuses the same `db_session` (real
    Postgres, rolled back by the fixture, never mocked)."""

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


def _registro_payload(**overrides: object) -> dict:
    import uuid

    payload: dict[str, object] = {
        "email": f"nueva-cuenta-{uuid.uuid4()}@example.com",
        "password": "contrasena-segura-123",
        "nombre": "Laura Gomez",
        "rol": "propietario",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# POST /usuarios/registro
# ---------------------------------------------------------------------------


class TestPostUsuariosRegistroSuccess:
    async def test_should_return_201_with_valid_jwt_when_registering_as_propietario(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/usuarios/registro", json=_registro_payload(rol="propietario")
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        payload = decode_access_token(body["access_token"])
        assert payload.sub == body["usuario"]["id"]
        assert payload.rol == "propietario"
        assert body["usuario"]["rol"] == "propietario"
        assert "password" not in body["usuario"]
        assert "password_hash" not in body["usuario"]

    async def test_should_return_201_with_valid_jwt_when_registering_as_agente(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post("/usuarios/registro", json=_registro_payload(rol="agente"))

        # Assert
        assert response.status_code == 201
        body = response.json()
        payload = decode_access_token(body["access_token"])
        assert payload.rol == "agente"
        assert body["usuario"]["rol"] == "agente"

    async def test_should_return_201_with_valid_jwt_when_registering_as_inquilino(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/usuarios/registro", json=_registro_payload(rol="inquilino")
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        payload = decode_access_token(body["access_token"])
        assert payload.rol == "inquilino"
        assert body["usuario"]["rol"] == "inquilino"

    async def test_should_persist_the_new_usuario_and_make_it_loginable(
        self, client: httpx.AsyncClient
    ) -> None:
        # Arrange
        email = _registro_payload()["email"]
        payload = _registro_payload(email=email, password="contrasena-segura-123")

        # Act
        registro_response = await client.post("/usuarios/registro", json=payload)
        login_response = await client.post(
            "/usuarios/login", json={"email": email, "password": "contrasena-segura-123"}
        )

        # Assert
        assert registro_response.status_code == 201
        assert login_response.status_code == 200
        assert login_response.json()["usuario"]["email"] == email


class TestPostUsuariosRegistroRejectedCases:
    async def test_should_return_409_when_email_already_registered(
        self, client: httpx.AsyncClient
    ) -> None:
        # Arrange
        payload = _registro_payload()
        await client.post("/usuarios/registro", json=payload)

        # Act: same email, different password/nombre/rol is irrelevant — the
        # email alone must trigger the rejection.
        response = await client.post(
            "/usuarios/registro",
            json=_registro_payload(email=payload["email"], rol="inquilino"),
        )

        # Assert
        assert response.status_code == 409

    async def test_should_return_422_when_email_field_is_missing(
        self, client: httpx.AsyncClient
    ) -> None:
        # Arrange
        payload = _registro_payload()
        del payload["email"]

        # Act
        response = await client.post("/usuarios/registro", json=payload)

        # Assert
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /usuarios/login
# ---------------------------------------------------------------------------


class TestPostUsuariosLoginSuccess:
    async def test_should_return_200_with_valid_jwt_when_credentials_are_correct(
        self, client: httpx.AsyncClient
    ) -> None:
        # Arrange
        payload = _registro_payload(password="clave-correcta-123")
        await client.post("/usuarios/registro", json=payload)

        # Act
        response = await client.post(
            "/usuarios/login",
            json={"email": payload["email"], "password": "clave-correcta-123"},
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        decoded = decode_access_token(body["access_token"])
        assert decoded.sub == body["usuario"]["id"]
        assert decoded.rol == body["usuario"]["rol"]


class TestPostUsuariosLoginRejectedCases:
    async def test_should_reject_login_with_nonexistent_email_and_wrong_password_identically(
        self, client: httpx.AsyncClient
    ) -> None:
        """Both rejection causes — unknown email vs. wrong password for a
        known email — must be indistinguishable to the caller (spec.md
        "Login rechazado sin revelar cuál dato falló")."""
        # Arrange
        payload = _registro_payload(password="clave-correcta-123")
        await client.post("/usuarios/registro", json=payload)

        # Act
        response_email_inexistente = await client.post(
            "/usuarios/login",
            json={"email": "no-existe@example.com", "password": "cualquier-cosa"},
        )
        response_password_incorrecta = await client.post(
            "/usuarios/login",
            json={"email": payload["email"], "password": "clave-incorrecta"},
        )

        # Assert: same status code and same response body in both cases.
        assert response_email_inexistente.status_code == 401
        assert response_password_incorrecta.status_code == 401
        assert response_email_inexistente.json() == response_password_incorrecta.json()
