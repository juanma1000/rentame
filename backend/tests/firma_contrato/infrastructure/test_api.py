"""Integration tests for the `firma-contrato` API layer (group 6 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`),
covering every scenario of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/seguro_arrendamiento/infrastructure/test_api.py`.

TDD Red phase: `main.py` registers no router for the `firma-contrato`
domain yet, and neither
`firma_contrato/infrastructure/api/router.py` nor `schemas.py` exist.
Every request is therefore expected to fail with FastAPI's default 404 (no
matching route). This file fixes, by construction, the exact contract
`backend-expert` must implement (tasks 6.2/6.4):

- `POST /firma-contrato/generar` — JSON body: `inmueble_id`,
  `nombre_inquilino`, `nombre_propietario`, `direccion_inmueble`,
  `canon_mensual`, `duracion_meses`. Requires
  `Authorization: Bearer <JWT inquilino>`. `200` with `{"id": "<uuid>",
  "estado": "enviado_a_firma", "referencia_externa": str}` when the
  account has an approved `PolizaArrendamiento` (`FakeAdapter` always
  accepts). Without one -> explicit error (domain `PolizaNoAprobada`),
  without generating a document.
- `POST /firma-contrato/webhook` — JSON body: `referencia_externa`,
  `estado` (`"firmado"`/`"rechazado"`/`"expirado"`). No auth required (this
  is called by the proveedor externo, not by an authenticated user of this
  app — same convention payment-gateway webhooks use elsewhere in the
  project). `firmado` creates an `ArrendamientoActivo`; `rechazado`/
  `expirado` does not and leaves the associated `PolizaArrendamiento`
  untouched.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from firma_contrato.infrastructure.persistence.models import ArrendamientoActivoORM, ContratoORM
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


class TestGenerarContratoEndpoint:
    async def test_should_return_200_with_estado_enviado_a_firma_when_poliza_aprobada(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        await _seed_poliza_aprobada(db_session, seed_inquilino.id)

        # Act
        response = await client.post(
            "/firma-contrato/generar",
            headers=_auth_header(seed_inquilino.id),
            json=_generar_payload(),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "enviado_a_firma"
        assert body["referencia_externa"]
        assert "id" in body

    async def test_should_reject_explicitly_when_no_poliza_aprobada(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/firma-contrato/generar",
            headers=_auth_header(seed_inquilino.id),
            json=_generar_payload(),
        )

        # Assert
        assert response.status_code in (403, 409)
        assert "detail" in response.json()

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.post("/firma-contrato/generar", json=_generar_payload())

        # Assert
        assert response.status_code == 401


class TestWebhookEndpoint:
    async def test_firmado_creates_arrendamiento_activo(
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
        referencia_externa = generar_response.json()["referencia_externa"]

        # Act
        response = await client.post(
            "/firma-contrato/webhook",
            json={"referencia_externa": referencia_externa, "estado": "firmado"},
        )

        # Assert
        assert response.status_code == 200
        resultado = await db_session.execute(
            select(ContratoORM).where(ContratoORM.referencia_externa == referencia_externa)
        )
        contrato = resultado.scalars().one()
        assert contrato.estado == "firmado"

        arrendamientos = await db_session.execute(
            select(ArrendamientoActivoORM).where(ArrendamientoActivoORM.contrato_id == contrato.id)
        )
        assert arrendamientos.scalars().one_or_none() is not None

    async def test_rechazado_does_not_create_arrendamiento_and_poliza_stays_aprobada(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        poliza_id = await _seed_poliza_aprobada(db_session, seed_inquilino.id)
        generar_response = await client.post(
            "/firma-contrato/generar",
            headers=_auth_header(seed_inquilino.id),
            json=_generar_payload(),
        )
        referencia_externa = generar_response.json()["referencia_externa"]

        # Act
        response = await client.post(
            "/firma-contrato/webhook",
            json={"referencia_externa": referencia_externa, "estado": "rechazado"},
        )

        # Assert
        assert response.status_code == 200
        resultado = await db_session.execute(
            select(ContratoORM).where(ContratoORM.referencia_externa == referencia_externa)
        )
        contrato = resultado.scalars().one()
        assert contrato.estado == "rechazado"

        arrendamientos = await db_session.execute(
            select(ArrendamientoActivoORM).where(ArrendamientoActivoORM.contrato_id == contrato.id)
        )
        assert arrendamientos.scalars().one_or_none() is None

        poliza = await db_session.get(PolizaArrendamientoORM, poliza_id)
        assert poliza is not None
        assert poliza.estado == "aprobada"

    async def test_expirado_does_not_create_arrendamiento(
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
        referencia_externa = generar_response.json()["referencia_externa"]

        # Act
        response = await client.post(
            "/firma-contrato/webhook",
            json={"referencia_externa": referencia_externa, "estado": "expirado"},
        )

        # Assert
        assert response.status_code == 200
        resultado = await db_session.execute(
            select(ContratoORM).where(ContratoORM.referencia_externa == referencia_externa)
        )
        contrato = resultado.scalars().one()
        assert contrato.estado == "expirado"

    async def test_returns_404_when_referencia_externa_not_found(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/firma-contrato/webhook",
            json={"referencia_externa": "no-existe", "estado": "firmado"},
        )

        # Assert
        assert response.status_code == 404
