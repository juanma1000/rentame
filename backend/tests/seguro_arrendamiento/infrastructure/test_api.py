"""Integration tests for the `seguro-arrendamiento` API layer (group 5 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`), covering every
scenario of
`openspec/changes/seguro-arrendamiento-inquilino/specs/seguro-arrendamiento/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/identidad/infrastructure/test_api.py`.

TDD Red phase: `POST /seguro-arrendamiento/contratar` does not exist yet —
`main.py` registers no router for the `seguro-arrendamiento` domain, and
neither `seguro_arrendamiento/infrastructure/api/router.py` nor
`schemas.py` exist. Every request is therefore expected to fail with
FastAPI's default 404 (no matching route). This file fixes, by
construction, the exact contract `backend-expert` must implement (task
5.3):

- `POST /seguro-arrendamiento/contratar` — `multipart/form-data`. Text
  field: `cedula` (required `Form`). Files: `documentos` (required `File`,
  at least one). Requires `Authorization: Bearer <JWT inquilino>`. `200`
  with `{"id": "<uuid>", "estado": "aprobada", "prima_mensual": float,
  "referencia_externa": str}` when the account has `identidad_verificada =
  True` (the default `FakeAdapter` always approves). Missing
  `cedula`/`documentos` -> `422` (FastAPI's own validation). An inquilino
  without `identidad_verificada = True` -> explicit error (domain
  `IdentidadNoVerificada`), without a provider call.

- The document bytes sent in any request must never end up in any table or
  file after the call — verified explicitly against
  `polizas_arrendamiento` (only the outcome fields, no binary column
  exists at all), same test shape as
  `tests/identidad/infrastructure/test_api.py`'s
  `TestValidarIdentidadNoPersistsImageBytes`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from sqlalchemy import select
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


class TestContratarSeguroArrendamientoEndpoint:
    async def test_should_return_200_with_estado_aprobada_when_identidad_verificada(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        await _marcar_identidad_verificada(db_session, seed_inquilino.id)

        # Act
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "aprobada"
        assert body["prima_mensual"] > 0
        assert body["referencia_externa"]
        assert "id" in body

    async def test_should_return_422_when_cedula_is_missing(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM, db_session: AsyncSession
    ) -> None:
        # Arrange
        await _marcar_identidad_verificada(db_session, seed_inquilino.id)

        # Act
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            files=_files(),
        )

        # Assert
        assert response.status_code == 422

    async def test_should_return_422_when_documentos_are_missing(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM, db_session: AsyncSession
    ) -> None:
        # Arrange
        await _marcar_identidad_verificada(db_session, seed_inquilino.id)

        # Act
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
        )

        # Assert
        assert response.status_code == 422

    async def test_should_reject_explicitly_when_identidad_not_verificada(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act (seed_inquilino defaults to identidad_verificada=False)
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert response.status_code in (403, 409)
        assert "detail" in response.json()

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert response.status_code == 401


class TestContratarSeguroArrendamientoNoPersistsDocumentBytes:
    async def test_document_bytes_never_reach_the_database(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        await _marcar_identidad_verificada(db_session, seed_inquilino.id)
        desprendible_bytes = b"contenido-secreto-desprendible"
        certificado_bytes = b"contenido-secreto-certificado"

        # Act
        response = await client.post(
            "/seguro-arrendamiento/contratar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=[
                ("documentos", ("desprendible.pdf", desprendible_bytes, "application/pdf")),
                ("documentos", ("certificado.pdf", certificado_bytes, "application/pdf")),
            ],
        )
        assert response.status_code == 200

        # Assert: `PolizaArrendamientoORM` has no column that could hold the
        # bytes — this asserts the model shape stays that way — and nothing
        # persisted equals either payload.
        columnas = {c.name for c in PolizaArrendamientoORM.__table__.columns}
        assert columnas == {
            "id",
            "usuario_id",
            "estado",
            "fecha",
            "prima_mensual",
            "vigencia_desde",
            "vigencia_hasta",
            "referencia_externa",
        }

        resultado = await db_session.execute(
            select(PolizaArrendamientoORM).where(
                PolizaArrendamientoORM.usuario_id == seed_inquilino.id
            )
        )
        modelo = resultado.scalars().one()
        for valor in (
            modelo.id,
            modelo.usuario_id,
            modelo.estado,
            modelo.fecha,
            modelo.prima_mensual,
            modelo.vigencia_desde,
            modelo.vigencia_hasta,
            modelo.referencia_externa,
        ):
            if isinstance(valor, bytes):
                assert valor not in (desprendible_bytes, certificado_bytes)
