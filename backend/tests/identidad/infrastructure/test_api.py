"""Integration tests for the `identidad` API layer (group 5 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`), covering every
scenario of
`openspec/changes/validacion-identidad-inquilino/specs/identidad/spec.md`
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_inquilino` from `backend/tests/conftest.py`) — no mocks,
following the precedent of `tests/agencias/infrastructure/test_api.py`.

TDD Red phase: `POST /identidad/validar` does not exist yet — `main.py`
registers no router for the `identidad` domain, and neither
`identidad/infrastructure/api/router.py` nor
`identidad/infrastructure/api/schemas.py` exist. Every request is therefore
expected to fail with FastAPI's default 404 (no matching route). This file
fixes, by construction, the exact contract `backend-expert` must implement
(task 5.3):

- `POST /identidad/validar` — `multipart/form-data`. Text field: `cedula`
  (required `Form`). Files: `imagen_frente`, `imagen_dorso` (required
  `File`). Requires `Authorization: Bearer <JWT inquilino>`. `200` with
  `{"id": "<uuid>", "estado": "aprobado", "referencia_externa": str}` when
  the account has no previous validación (the default `FakeAdapter` always
  approves). Missing `cedula`/`imagen_frente`/`imagen_dorso` -> `422`
  (FastAPI's own validation). A second attempt on an already-verified
  account -> `409` (domain `IdentidadYaVerificada`), without a second
  provider call (verified indirectly: the account stays verified with a
  single `ValidacionIdentidad` row).

- The image bytes sent in any request must never end up in any table or
  file after the call — verified explicitly against `validaciones_identidad`
  (only `cedula` as text, no binary column exists at all) and by asserting
  no file was written under a scratch directory the test points `TMPDIR`-like
  storage at (this project's endpoint proxies straight to the proveedor and
  never touches disk/object storage for images, unlike `inmuebles`' photo
  upload flow).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identidad.infrastructure.persistence.models import ValidacionIdentidadORM
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


class TestValidarIdentidadEndpoint:
    async def test_should_return_200_with_estado_aprobado_when_payload_is_valid(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "aprobado"
        assert body["referencia_externa"]
        assert "id" in body

    async def test_should_return_422_when_cedula_is_missing(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            files=_files(),
        )

        # Assert
        assert response.status_code == 422

    async def test_should_return_422_when_images_are_missing(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
        )

        # Assert
        assert response.status_code == 422

    async def test_should_return_409_when_cuenta_ya_verificada(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange: first attempt approves and verifies the account.
        primera = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )
        assert primera.status_code == 200

        # Act: second attempt on the same, now-verified account.
        segunda = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert segunda.status_code == 409
        assert "detail" in segunda.json()

        resultado = await db_session.execute(
            select(ValidacionIdentidadORM).where(
                ValidacionIdentidadORM.usuario_id == seed_inquilino.id
            )
        )
        assert len(resultado.scalars().all()) == 1

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.post(
            "/identidad/validar",
            data={"cedula": "1002003004"},
            files=_files(),
        )

        # Assert
        assert response.status_code == 401


class TestValidarIdentidadNoPersistsImageBytes:
    async def test_image_bytes_never_reach_the_database(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        frente_bytes = b"contenido-secreto-frente"
        dorso_bytes = b"contenido-secreto-dorso"

        # Act
        response = await client.post(
            "/identidad/validar",
            headers=_auth_header(seed_inquilino.id),
            data={"cedula": "1002003004"},
            files={
                "imagen_frente": ("frente.jpg", frente_bytes, "image/jpeg"),
                "imagen_dorso": ("dorso.jpg", dorso_bytes, "image/jpeg"),
            },
        )
        assert response.status_code == 200

        # Assert: `ValidacionIdentidadORM` has no column that could hold the
        # bytes — this asserts the model shape stays that way — and nothing
        # persisted equals either payload.
        columnas = {c.name for c in ValidacionIdentidadORM.__table__.columns}
        assert columnas == {"id", "usuario_id", "cedula", "estado", "fecha", "referencia_externa"}

        resultado = await db_session.execute(
            select(ValidacionIdentidadORM).where(
                ValidacionIdentidadORM.usuario_id == seed_inquilino.id
            )
        )
        modelo = resultado.scalars().one()
        for valor in (modelo.id, modelo.usuario_id, modelo.cedula, modelo.estado, modelo.fecha, modelo.referencia_externa):
            if isinstance(valor, bytes):
                assert valor not in (frente_bytes, dorso_bytes)
