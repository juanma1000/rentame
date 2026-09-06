"""Integration tests for `GET /firma-contrato/estado` (task 3.3 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`), covering every
scenario of
`openspec/changes/frontend-flujo-arrendamiento/specs/firma-contrato/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/firma_contrato/infrastructure/test_api.py`.

TDD Red phase: `GET /firma-contrato/estado` does not exist yet in
`firma_contrato/infrastructure/api/router.py`. Every request is therefore
expected to fail with FastAPI's default 404 (no matching route). This file
fixes, by construction, the exact contract `backend-expert` must implement
(task 3.4):

- `GET /firma-contrato/estado` — no body. Requires
  `Authorization: Bearer <JWT inquilino>`. `200` with
  `{"estado": "no_iniciado", "arrendamiento_activo_id": null}` when the
  account has no `Contrato`; `{"estado": "firmado",
  "arrendamiento_activo_id": "<uuid>"}` once the contrato is signed
  (via the `/firma-contrato/webhook` simulated by
  `tests/firma_contrato/infrastructure/test_api.py`). `401` without a
  token.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from seguro_arrendamiento.infrastructure.persistence.models import PolizaArrendamientoORM
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


def _generar_payload() -> dict[str, object]:
    return {
        "inmueble_id": str(uuid.uuid4()),
        "nombre_inquilino": "Juan Pérez",
        "nombre_propietario": "María Gómez",
        "direccion_inmueble": "Calle 10 # 20-30, Cali",
        "canon_mensual": 1500000.0,
        "duracion_meses": 12,
    }


async def _seed_poliza_aprobada(db_session: AsyncSession, usuario_id: uuid.UUID) -> uuid.UUID:
    poliza = PolizaArrendamientoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        estado="aprobada",
        fecha=datetime.now(UTC),
    )
    db_session.add(poliza)
    await db_session.flush()
    return poliza.id


class TestConsultarEstadoFirmaEndpoint:
    async def test_should_return_no_iniciado_when_no_contrato_exists(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.get(
            "/firma-contrato/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"estado": "no_iniciado", "arrendamiento_activo_id": None}

    async def test_should_return_firmado_with_arrendamiento_activo_id_after_webhook(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        generar_response = await client.post(
            "/firma-contrato/generar",
            headers=_auth_header(seed_inquilino.id),
            json=_generar_payload(),
        )
        assert generar_response.status_code == 200
        referencia_externa = generar_response.json()["referencia_externa"]

        webhook_response = await client.post(
            "/firma-contrato/webhook",
            json={"referencia_externa": referencia_externa, "estado": "firmado"},
        )
        assert webhook_response.status_code == 200

        # Act
        response = await client.get(
            "/firma-contrato/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "firmado"
        assert body["arrendamiento_activo_id"]

    async def test_should_return_enviado_a_firma_without_arrendamiento_activo_id(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        generar_response = await client.post(
            "/firma-contrato/generar",
            headers=_auth_header(seed_inquilino.id),
            json=_generar_payload(),
        )
        assert generar_response.status_code == 200

        # Act
        response = await client.get(
            "/firma-contrato/estado", headers=_auth_header(seed_inquilino.id)
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "enviado_a_firma"
        assert body["arrendamiento_activo_id"] is None

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.get("/firma-contrato/estado")

        # Assert
        assert response.status_code == 401
