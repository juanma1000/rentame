"""Integration tests for the `inmuebles` API layer (group 7 of
`openspec/changes/hu-001/tasks.md`), covering every scenario of
`openspec/changes/hu-001/specs/inmuebles/spec.md` end-to-end through real
HTTP requests against the real FastAPI app (`main.app`), a real PostgreSQL
test database (`rentame_test`, via `db_session`/`seed_propietario` from
`backend/tests/conftest.py`) and real MinIO (no mocks anywhere).

TDD Red phase: none of `POST /inmuebles/`, `PUT /inmuebles/{id}`,
`PATCH /inmuebles/{id}/disponibilidad` or `GET /inmuebles/mios` exist yet —
`main.py` registers no router for this domain. Every request below is
therefore expected to fail with FastAPI's default 404 (no matching route),
not with an import error, since this file only imports `main.app` plus
already-existing collaborators (`InmuebleRepositoryPostgres`, domain
entities, the JWT test helper). This file fixes, by construction, the exact
contract `backend-expert` must implement:

- `POST /inmuebles/` — `multipart/form-data`. Text fields: `direccion`,
  `barrio`, `ciudad`, `tipo`, `area_m2`, `habitaciones`, `banos`,
  `valor_mensual`, `descripcion` (all required `Form` fields). Files:
  1 to `MAX_FOTOS_INMUEBLE` (10) parts named `fotos` (repeated). Requires
  `Authorization: Bearer <JWT propietario>`. Returns `201` with an
  `InmuebleResponse` JSON body (see shape below) with `estado ==
  "disponible"`. Missing a required `Form` field -> `422` (FastAPI's own
  validation). Missing `fotos` entirely, or more than 10 `fotos` parts ->
  `422` (domain `DomainValidationError` from `Inmueble.crear`, mapped to
  `HTTP_422_UNPROCESSABLE_ENTITY` with body `{"detail": "<message>"}`).
  Missing/invalid JWT -> `401`.

- `PUT /inmuebles/{inmueble_id}` — JSON body `InmuebleEditRequest` (same
  editable fields as above, no `fotos`). Requires
  `Authorization: Bearer <JWT propietario>` and only succeeds (`200`,
  updated `InmuebleResponse`) when the JWT's `sub` matches
  `Inmueble.propietario_id`. `PropietarioInvalido` -> `403`.
  `InmuebleNoEncontrado` -> `404`. Both mapped to
  `{"detail": "<message>"}`.

- `PATCH /inmuebles/{inmueble_id}/disponibilidad` — JSON body
  `{"nuevo_estado": "disponible" | "oculto"}`. Same ownership semantics as
  `PUT` (`403`/`404`). Returns `200` with the updated `InmuebleResponse`
  (`estado` reflects the transition).

- `GET /inmuebles/mios` — no body. Requires
  `Authorization: Bearer <JWT propietario>`. Returns `200` with a JSON
  array of `InmuebleResponse`, containing only `Inmueble`s owned by the
  JWT's `sub` (empty array `[]` when the propietario has none).

`InmuebleResponse` JSON shape (both as the `POST`/`PUT`/`PATCH` body and as
each element of the `GET /inmuebles/mios` array):
```
{
  "id": "<uuid>",
  "propietario_id": "<uuid>",
  "direccion": str,
  "barrio": str,
  "ciudad": str,
  "tipo": str,
  "area_m2": number,
  "habitaciones": int,
  "banos": int,
  "valor_mensual": number,
  "descripcion": str,
  "estado": "disponible" | "oculto" | "no_disponible",
  "fotos": [
    {"url_storage": str, "storage_key": str, "orden": int, "es_principal": bool},
    ...
  ]
}
```
`storage_key` is included in the response (not just `url_storage`) so
callers — including this test file — can address/clean up the exact object
in MinIO without having to re-derive it.

The `PATCH /inmuebles/{id}/disponibilidad` endpoint only accepts
`"disponible"`/`"oculto"` as `nuevo_estado` — `"no_disponible"` is reached
exclusively via a future internal caller (the `arrendamiento` use case,
HU-005), never through this HTTP endpoint, per `design.md` decisión 4.

Every test that persists an `Inmueble` relies on `db_session`'s per-test
rollback (see `backend/tests/conftest.py`) for Postgres cleanup — the
`client` fixture below overrides `get_db_session` with that same session
instance so every request in a test shares one transaction, exactly like
`test_repository.py` already does with direct repository calls. Any photo
actually uploaded to the real MinIO bucket during a successful `POST` is
deleted in a `finally` block via a raw `boto3` client, mirroring
`test_storage_adapter.py`'s cleanup pattern.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import boto3
import httpx
import pytest
import pytest_asyncio
from botocore.client import BaseClient, Config
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from main import app
from shared.infrastructure.database import get_db_session
from shared.infrastructure.settings import Settings, get_settings
from tests.utils.auth import build_valid_token
from usuarios.infrastructure.persistence.models import UsuarioORM

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """`httpx.AsyncClient` bound to the real `main.app`, with `get_db_session`
    overridden so every request in a test reuses the same `db_session`
    (same pattern `test_repository.py` uses directly against the
    repository) — real Postgres, rolled back by the fixture, never mocked.
    """

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="module")
def raw_s3_client(settings: Settings) -> BaseClient:
    """A boto3 client independent of the API under test, used only to clean
    up photos the API actually uploads to the real MinIO bucket during a
    successful `POST /inmuebles/`."""
    client_ = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,
        config=Config(signature_version="s3v4"),
    )
    try:
        client_.head_bucket(Bucket=settings.storage_bucket_name)
    except ClientError:
        client_.create_bucket(Bucket=settings.storage_bucket_name)
    return client_


@pytest_asyncio.fixture
async def otro_propietario(db_session: AsyncSession) -> UsuarioORM:
    """A second "propietario" user, distinct from `seed_propietario`, used by
    every ownership-rejection scenario."""
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"otro-propietario-{uuid.uuid4()}@example.com",
        rol="propietario",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


# ---------------------------------------------------------------------------
# Test data builders
# ---------------------------------------------------------------------------


def _auth_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "propietario")
    return {"Authorization": f"Bearer {token}"}


def _valid_form_fields(**overrides: str) -> dict[str, str]:
    fields = {
        "direccion": "Calle 10 # 20-30",
        "barrio": "El Poblado",
        "ciudad": "Medellin",
        "tipo": "apartamento",
        "area_m2": "65.5",
        "habitaciones": "2",
        "banos": "2",
        "valor_mensual": "1500000",
        "descripcion": "Apartamento amoblado cerca al metro",
    }
    fields.update(overrides)
    return fields


def _fake_photo_file(name: str = "foto.jpg") -> tuple[str, tuple[str, bytes, str]]:
    return ("fotos", (name, f"fake-jpeg-bytes-{uuid.uuid4()}".encode(), "image/jpeg"))


def _fake_photos(count: int) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [_fake_photo_file(name=f"foto-{n}.jpg") for n in range(1, count + 1)]


def _build_foto(orden: int = 1, *, es_principal: bool = False) -> FotoInmueble:
    return FotoInmueble(
        url_storage=f"https://storage.example.com/inmuebles/fotos/{orden}.jpg",
        storage_key=f"inmuebles/fotos/{orden}.jpg",
        orden=orden,
        es_principal=es_principal,
    )


def _build_inmueble(
    propietario_id: uuid.UUID, *, fotos_count: int = 1, **overrides: object
) -> Inmueble:
    fotos = [_build_foto(orden=n, es_principal=(n == 1)) for n in range(1, fotos_count + 1)]
    kwargs: dict[str, object] = {
        "propietario_id": propietario_id,
        "direccion": "Calle 10 # 20-30",
        "barrio": "El Poblado",
        "ciudad": "Medellin",
        "tipo": "apartamento",
        "area_m2": Decimal("65.5"),
        "habitaciones": 2,
        "banos": 2,
        "valor_mensual": Decimal("1500000"),
        "descripcion": "Apartamento amoblado cerca al metro",
        "fotos": fotos,
    }
    kwargs.update(overrides)
    return Inmueble.crear(**kwargs)  # type: ignore[arg-type]


async def _seed_inmueble(
    db_session: AsyncSession, propietario_id: uuid.UUID, **overrides: object
) -> Inmueble:
    repository = InmuebleRepositoryPostgres(db_session)
    inmueble = _build_inmueble(propietario_id, **overrides)
    guardado = await repository.guardar(inmueble)
    await db_session.flush()
    return guardado


def _delete_fotos_from_minio(raw_s3_client: BaseClient, settings: Settings, body: dict) -> None:
    for foto in body.get("fotos", []):
        storage_key = foto.get("storage_key")
        if storage_key:
            raw_s3_client.delete_object(Bucket=settings.storage_bucket_name, Key=storage_key)


# ---------------------------------------------------------------------------
# POST /inmuebles/
# ---------------------------------------------------------------------------


class TestPostInmueblesSuccess:
    async def test_should_return_201_and_estado_disponible_when_valid_data_and_one_foto(
        self,
        client: httpx.AsyncClient,
        seed_propietario: UsuarioORM,
        raw_s3_client: BaseClient,
        settings: Settings,
    ) -> None:
        # Arrange
        response_body: dict = {}

        try:
            # Act
            response = await client.post(
                "/inmuebles/",
                data=_valid_form_fields(),
                files=[_fake_photo_file()],
                headers=_auth_header(seed_propietario.id),
            )

            # Assert
            assert response.status_code == 201
            response_body = response.json()
            assert response_body["id"] is not None
            assert response_body["estado"] == "disponible"
            assert response_body["propietario_id"] == str(seed_propietario.id)
            assert response_body["direccion"] == "Calle 10 # 20-30"
            assert response_body["valor_mensual"] == 1500000
            assert len(response_body["fotos"]) == 1
        finally:
            _delete_fotos_from_minio(raw_s3_client, settings, response_body)


class TestPostInmueblesRejectedCases:
    async def test_should_return_422_when_no_fotos_attached(
        self, client: httpx.AsyncClient, seed_propietario: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(),
            headers=_auth_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 422

    async def test_should_return_422_when_more_than_ten_fotos_attached(
        self,
        client: httpx.AsyncClient,
        seed_propietario: UsuarioORM,
        raw_s3_client: BaseClient,
        settings: Settings,
    ) -> None:
        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(),
            files=_fake_photos(11),
            headers=_auth_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 422

    async def test_should_return_401_when_authorization_header_is_missing(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(),
            files=[_fake_photo_file()],
        )

        # Assert
        assert response.status_code == 401

    async def test_should_return_422_when_valor_mensual_field_is_missing(
        self, client: httpx.AsyncClient, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        fields = _valid_form_fields()
        del fields["valor_mensual"]

        # Act
        response = await client.post(
            "/inmuebles/",
            data=fields,
            files=[_fake_photo_file()],
            headers=_auth_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /inmuebles/{id}
# ---------------------------------------------------------------------------


def _edit_payload(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "direccion": "Carrera 50 # 10-20",
        "barrio": "Laureles",
        "ciudad": "Medellin",
        "tipo": "apartamento",
        "area_m2": "70.0",
        "habitaciones": 3,
        "banos": 2,
        "valor_mensual": "1800000",
        "descripcion": "Apartamento renovado con balcón",
    }
    payload.update(overrides)
    return payload


class TestPutInmuebleSuccess:
    async def test_should_return_200_and_update_data_when_caller_is_the_owner(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        inmueble = await _seed_inmueble(db_session, seed_propietario.id)

        # Act
        response = await client.put(
            f"/inmuebles/{inmueble.id}",
            json=_edit_payload(),
            headers=_auth_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(inmueble.id)
        assert body["direccion"] == "Carrera 50 # 10-20"
        assert body["barrio"] == "Laureles"
        assert body["valor_mensual"] == 1800000


class TestPutInmuebleRejectedCases:
    async def test_should_return_403_when_caller_is_not_the_owner(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
        otro_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        inmueble = await _seed_inmueble(db_session, seed_propietario.id)

        # Act
        response = await client.put(
            f"/inmuebles/{inmueble.id}",
            json=_edit_payload(),
            headers=_auth_header(otro_propietario.id),
        )

        # Assert
        assert response.status_code == 403

    async def test_should_return_404_when_inmueble_does_not_exist(
        self, client: httpx.AsyncClient, seed_propietario: UsuarioORM
    ) -> None:
        # Arrange
        inmueble_id = uuid.uuid4()

        # Act
        response = await client.put(
            f"/inmuebles/{inmueble_id}",
            json=_edit_payload(),
            headers=_auth_header(seed_propietario.id),
        )

        # Assert: must be the *domain* "not found" (InmuebleNoEncontrado,
        # message references the requested id), not FastAPI's generic
        # "route not found" 404 (which would coincidentally also be a 404
        # today, before the router exists, with body {"detail": "Not Found"})
        assert response.status_code == 404
        assert str(inmueble_id) in response.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /inmuebles/{id}/disponibilidad
# ---------------------------------------------------------------------------


class TestPatchDisponibilidadSuccess:
    async def test_should_despublicar_then_republicar_successfully_for_the_owner(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        inmueble = await _seed_inmueble(db_session, seed_propietario.id)
        assert inmueble.estado == EstadoInmueble.DISPONIBLE

        # Act: despublicar
        despublicar_response = await client.patch(
            f"/inmuebles/{inmueble.id}/disponibilidad",
            json={"nuevo_estado": "oculto"},
            headers=_auth_header(seed_propietario.id),
        )

        # Assert: despublicar
        assert despublicar_response.status_code == 200
        assert despublicar_response.json()["estado"] == "oculto"

        # Act: republicar
        republicar_response = await client.patch(
            f"/inmuebles/{inmueble.id}/disponibilidad",
            json={"nuevo_estado": "disponible"},
            headers=_auth_header(seed_propietario.id),
        )

        # Assert: republicar
        assert republicar_response.status_code == 200
        assert republicar_response.json()["estado"] == "disponible"


class TestPatchDisponibilidadRejectedCases:
    async def test_should_return_403_when_caller_is_not_the_owner(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
        otro_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        inmueble = await _seed_inmueble(db_session, seed_propietario.id)

        # Act
        response = await client.patch(
            f"/inmuebles/{inmueble.id}/disponibilidad",
            json={"nuevo_estado": "oculto"},
            headers=_auth_header(otro_propietario.id),
        )

        # Assert
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /inmuebles/mios
# ---------------------------------------------------------------------------


class TestGetMisInmuebles:
    async def test_should_return_only_inmuebles_owned_by_the_authenticated_propietario(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
        otro_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        propio_1 = await _seed_inmueble(db_session, seed_propietario.id, direccion="Calle 1 # 1-01")
        propio_2 = await _seed_inmueble(db_session, seed_propietario.id, direccion="Calle 2 # 2-02")
        await _seed_inmueble(db_session, otro_propietario.id, direccion="Calle 99 # 99-99")

        # Act
        response = await client.get("/inmuebles/mios", headers=_auth_header(seed_propietario.id))

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert {item["id"] for item in body} == {str(propio_1.id), str(propio_2.id)}
        assert all(item["propietario_id"] == str(seed_propietario.id) for item in body)

    async def test_should_return_empty_list_when_propietario_has_no_inmuebles(
        self, client: httpx.AsyncClient, seed_propietario: UsuarioORM
    ) -> None:
        # Act
        response = await client.get("/inmuebles/mios", headers=_auth_header(seed_propietario.id))

        # Assert
        assert response.status_code == 200
        assert response.json() == []
