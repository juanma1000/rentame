"""Integration tests for `GET /identidad/estado` (task 1.3 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`), covering every
scenario of
`openspec/changes/frontend-flujo-arrendamiento/specs/identidad/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/identidad/infrastructure/test_api.py`.

TDD Red phase: `GET /identidad/estado` does not exist yet in
`identidad/infrastructure/api/router.py`. Every request is therefore
expected to fail with FastAPI's default 404 (no matching route). This file
fixes, by construction, the exact contract `backend-expert` must implement
(task 1.4):

- `GET /identidad/estado` — no body. Requires
  `Authorization: Bearer <JWT inquilino>`. `200` with
  `{"estado": "no_iniciado"}` when the account has no
  `ValidacionIdentidad`; `{"estado": "aprobado"}` once one exists and is
  approved. `401` without a token.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from shared.infrastructure.database import get_db_session
from tests.utils.auth import build_valid_token
from usuarios.infrastructure.persistence.models import UsuarioORM


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """`httpx.AsyncClient` bound to the real `main.app`, with `get_db_session`
    overridden so every request in a test reuses the same `db_session` —
    real Postgres, rolled back by the fixture, never mocked."""

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


def _auth_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "inquilino")
    return {"Authorization": f"Bearer {token}"}


def _files() -> dict[str, tuple[str, bytes, str]]:
    return {
        "imagen_frente": ("frente.jpg", b"bytes-frente-cedula", "image/jpeg"),
        "imagen_dorso": ("dorso.jpg", b"bytes-dorso-cedula", "image/jpeg"),
    }


class TestConsultarEstadoIdentidadEndpoint:
    async def test_should_return_no_iniciado_when_no_validacion_exists(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.get(
            "/identidad/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"estado": "no_iniciado"}

    async def test_should_return_aprobado_after_a_successful_validacion(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Arrange: FakeAdapter always approves.
        validar = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )
        assert validar.status_code == 200

        # Act
        response = await client.get(
            "/identidad/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"estado": "aprobado"}

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.get("/identidad/estado")

        # Assert
        assert response.status_code == 401
