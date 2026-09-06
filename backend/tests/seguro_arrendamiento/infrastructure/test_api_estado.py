"""Integration tests for `GET /seguro-arrendamiento/estado` (task 2.3 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`), covering every
scenario of
`openspec/changes/frontend-flujo-arrendamiento/specs/seguro-arrendamiento/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/seguro_arrendamiento/infrastructure/test_api.py`.

TDD Red phase: `GET /seguro-arrendamiento/estado` does not exist yet in
`seguro_arrendamiento/infrastructure/api/router.py`. Every request is
therefore expected to fail with FastAPI's default 404 (no matching route).
This file fixes, by construction, the exact contract `backend-expert` must
implement (task 2.4):

- `GET /seguro-arrendamiento/estado` — no body. Requires
  `Authorization: Bearer <JWT inquilino>`. `200` with
  `{"estado": "no_iniciado", "prima_mensual": null}` when the account has
  no `PolizaArrendamiento`; `{"estado": "aprobada", "prima_mensual":
  <float>}` once one exists and is approved. `401` without a token.
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


def _files() -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("documentos", ("desprendible.pdf", b"bytes-desprendible", "application/pdf")),
        ("documentos", ("certificado.pdf", b"bytes-certificado", "application/pdf")),
    ]


async def _marcar_identidad_verificada(db_session: AsyncSession, usuario_id: uuid.UUID) -> None:
    modelo = await db_session.get(UsuarioORM, usuario_id)
    assert modelo is not None
    modelo.identidad_verificada = True
    await db_session.flush()


class TestConsultarEstadoSeguroEndpoint:
    async def test_should_return_no_iniciado_when_no_poliza_exists(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.get(
            "/seguro-arrendamiento/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"estado": "no_iniciado", "prima_mensual": None}

    async def test_should_return_aprobada_with_prima_mensual_after_contratacion(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange: FakeAdapter always approves; needs identidad_verificada.
        await _marcar_identidad_verificada(db_session, seed_inquilino.id)
        contratar = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )
        assert contratar.status_code == 200

        # Act
        response = await client.get(
            "/seguro-arrendamiento/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "aprobada"
        assert body["prima_mensual"] > 0

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.get("/seguro-arrendamiento/estado")

        # Assert
        assert response.status_code == 401
