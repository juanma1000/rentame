"""Integration tests for the agente-facing surface of the `inmuebles` API
layer (group 6 of `openspec/changes/hu-002/tasks.md`), covering every
`agente`-related scenario of `openspec/changes/hu-002/specs/inmuebles/
spec.md` end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_propietario`/`seed_agente` from
`backend/tests/conftest.py`) and real MinIO (no mocks anywhere) — same
infra precedent as `tests/inmuebles/infrastructure/test_api.py` (HU-001) and
`tests/agencias/infrastructure/test_api.py` (HU-007).

Kept in its own file (not merged into `test_api.py`) so the HU-001
propietario-only contract stays untouched and easy to diff, per the task
delegation instructions for this change.

TDD Red phase: as of this file, `inmuebles/infrastructure/api/router.py`
still only knows about `get_current_propietario` — it has no
`propietario_id` form field on `POST /inmuebles/`, no cross-domain
authorization against `agencias`, no `agente_id` on `InmuebleResponse`, and
no `GET /inmuebles/gestionados` route at all. Every test below is expected
to fail for one of these reasons (not import/collection errors, since this
file only imports already-existing collaborators): `POST`/`PUT`/`PATCH`
requests from an agente will get treated exactly like a propietario request
today (ignoring `propietario_id`, never checking `agencias`), so the
success cases fail their assertions (`agente_id` key absent, wrong
`propietario_id`, or the request outright succeeding when it must be
`403`); and `GET /inmuebles/gestionados` returns FastAPI's generic 404
(no matching route).

This file fixes, by construction, the exact contract `backend-expert` must
implement for group 6:

- `POST /inmuebles/` gains an optional multipart `Form` field
  `propietario_id` (UUID as string). Requires
  `Authorization: Bearer <JWT propietario-or-agente>` (`get_current_
  publicador`). When the caller's role is `agente`:
    - `propietario_id` becomes REQUIRED — if absent, `422` (no inmueble
      created).
    - the router resolves the agente's own `agencia_id`
      (`UsuarioAgenciaRepositoryPort.obtener_agencia_id`) and the
      `propietario_id`'s current active relación
      (`RelacionRepositoryPort.obtener_activa_por_propietario`); if there is
      none, or it belongs to a different agencia, `403` (no inmueble
      created, no photo uploaded to MinIO).
    - on success: `201`, `InmuebleResponse.propietario_id` is the
      *represented* propietario (not the agente), and a new
      `InmuebleResponse.agente_id` field equals the calling agente's id.
  When the caller's role is `propietario`, behavior is unchanged from
  HU-001 (`propietario_id` in the form, if present, is ignored;
  `agente_id` in the response is `null`).

- `InmuebleResponse` gains `agente_id: uuid.UUID | None`, alongside every
  HU-001 field, on every endpoint's response body (`POST`, `PUT`,
  `PATCH /disponibilidad`, `GET /mios`, `GET /gestionados`).

- `PUT /inmuebles/{id}` and `PATCH /inmuebles/{id}/disponibilidad`: the
  router first loads the `Inmueble` to learn its real `propietario_id`,
  then authorizes either (a) the caller is that propietario, or (b) the
  caller is an agente whose agencia has an `activa` relación with that
  propietario — regardless of whether that particular agente is the one
  who originally published it (`Inmueble.agente_id` is never consulted for
  authorization, only for the response body, and is never mutated by
  either endpoint). Any other caller -> `403`, no mutation. On success,
  same `200` + updated `InmuebleResponse` shape as HU-001.

- `GET /inmuebles/gestionados` (new route). Requires
  `Authorization: Bearer <JWT agente>` (`get_current_agente`). Resolves
  every `propietario_id` with an `activa` relación with the caller's
  agencia (via `agencias`' repositories) and returns `200` with a JSON
  array of `InmuebleResponse` for every `Inmueble` owned by any of those
  propietarios (empty array `[]` when the agente's agencia manages none,
  same convention as `GET /inmuebles/mios`).

Every test that persists an `Agencia`/`RelacionAgenciaPropietario` seeds it
directly against the real `agencias` repositories
(`AgenciaRepositoryPostgres`, `RelacionRepositoryPostgres`,
`UsuarioAgenciaRepositoryPostgres`), exactly like
`tests/agencias/infrastructure/test_api.py` already does — never through
HTTP, since this file is only exercising the `inmuebles` surface. Every test
that persists an `Inmueble` directly (bypassing `POST /inmuebles/`) uses
`InmuebleRepositoryPostgres` + `Inmueble.crear(..., agente_id=...)`, the
same helper pattern `tests/agencias/infrastructure/test_api.py` documents as
a stopgap until this very change lands the public API support (now it does,
for `POST`, but direct seeding is still simpler/faster for `PUT`/`PATCH`/
`GET` fixtures that don't exercise `POST` itself).
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

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario
from agencias.infrastructure.persistence.repository import (
    AgenciaRepositoryPostgres,
    RelacionRepositoryPostgres,
    UsuarioAgenciaRepositoryPostgres,
)
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
    """Same pattern as `tests/inmuebles/infrastructure/test_api.py`: a real
    `main.app` behind `httpx.AsyncClient`, with `get_db_session` overridden
    so every request in a test shares `db_session` (real Postgres, rolled
    back by the fixture)."""

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
    """Boto3 client independent of the API under test, used only to clean up
    photos actually uploaded to MinIO by a successful `POST /inmuebles/`."""
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
async def segundo_agente(db_session: AsyncSession) -> UsuarioORM:
    """A second "agente" user, distinct from `seed_agente` — used by the
    "another agente of the same agencia edits" scenarios."""
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"segundo-agente-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


@pytest_asyncio.fixture
async def agente_otra_agencia(db_session: AsyncSession) -> UsuarioORM:
    """A third "agente" user, member of a *different* agencia — used by the
    "agente without an active relación" rejection scenarios."""
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"agente-otra-agencia-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


@pytest_asyncio.fixture
async def otro_propietario(db_session: AsyncSession) -> UsuarioORM:
    """A second "propietario" user, distinct from `seed_propietario` — used
    by the `GET /inmuebles/gestionados` filtering scenario."""
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


def _agente_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "agente")
    return {"Authorization": f"Bearer {token}"}


def _propietario_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "propietario")
    return {"Authorization": f"Bearer {token}"}


def _valid_form_fields(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
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


def _delete_fotos_from_minio(raw_s3_client: BaseClient, settings: Settings, body: dict) -> None:
    for foto in body.get("fotos", []):
        storage_key = foto.get("storage_key")
        if storage_key:
            raw_s3_client.delete_object(Bucket=settings.storage_bucket_name, Key=storage_key)


async def _seed_agencia(
    db_session: AsyncSession, *, miembro_id: uuid.UUID | None = None
) -> Agencia:
    repository = AgenciaRepositoryPostgres(db_session)
    agencia = await repository.guardar(
        Agencia.crear(razon_social="Agencia Test HU-002", nit="900555666")
    )
    if miembro_id is not None:
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(miembro_id, agencia.id)
    await db_session.flush()
    return agencia


async def _seed_relacion(
    db_session: AsyncSession,
    *,
    agencia_id: uuid.UUID,
    propietario_id: uuid.UUID,
    estado: str = "activa",
) -> RelacionAgenciaPropietario:
    """`estado` is one of `"pendiente"`, `"activa"`, `"revocada"`."""
    repository = RelacionRepositoryPostgres(db_session)
    relacion = await repository.guardar(
        RelacionAgenciaPropietario.crear(agencia_id=agencia_id, propietario_id=propietario_id)
    )
    if estado in ("activa", "revocada"):
        relacion.activar()
        relacion = await repository.actualizar(relacion)
    if estado == "revocada":
        relacion.revocar()
        relacion = await repository.actualizar(relacion)
    await db_session.flush()
    return relacion


def _build_inmueble(
    propietario_id: uuid.UUID, *, agente_id: uuid.UUID | None = None, **overrides: object
) -> Inmueble:
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
        "fotos": [
            FotoInmueble(
                url_storage="https://storage.example.com/inmuebles/fotos/1.jpg",
                storage_key="inmuebles/fotos/1.jpg",
                orden=1,
                es_principal=True,
            )
        ],
        "agente_id": agente_id,
    }
    kwargs.update(overrides)
    return Inmueble.crear(**kwargs)  # type: ignore[arg-type]


async def _seed_inmueble(
    db_session: AsyncSession,
    propietario_id: uuid.UUID,
    *,
    agente_id: uuid.UUID | None = None,
    **overrides: object,
) -> Inmueble:
    repository = InmuebleRepositoryPostgres(db_session)
    inmueble = _build_inmueble(propietario_id, agente_id=agente_id, **overrides)
    guardado = await repository.guardar(inmueble)
    await db_session.flush()
    return guardado


# ---------------------------------------------------------------------------
# POST /inmuebles/ como agente
# ---------------------------------------------------------------------------


class TestPostInmueblesAgenteSuccess:
    async def test_should_return_201_with_agente_id_when_agencia_has_active_relacion(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
        raw_s3_client: BaseClient,
        settings: Settings,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        response_body: dict = {}

        try:
            # Act
            response = await client.post(
                "/inmuebles/",
                data=_valid_form_fields(propietario_id=str(seed_propietario.id)),
                files=[_fake_photo_file()],
                headers=_agente_header(seed_agente.id),
            )

            # Assert
            assert response.status_code == 201
            response_body = response.json()
            assert response_body["propietario_id"] == str(seed_propietario.id)
            assert response_body["agente_id"] == str(seed_agente.id)
            assert response_body["estado"] == "disponible"
        finally:
            _delete_fotos_from_minio(raw_s3_client, settings, response_body)


class TestPostInmueblesAgenteRejectedCases:
    async def test_should_return_403_and_not_create_when_agencia_has_no_relacion_at_all(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: seed_agente belongs to an agencia, but that agencia has
        # never had any relación with seed_propietario.
        await _seed_agencia(db_session, miembro_id=seed_agente.id)

        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(propietario_id=str(seed_propietario.id)),
            files=[_fake_photo_file()],
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 403
        inmuebles = await InmuebleRepositoryPostgres(db_session).listar_por_propietarios(
            [seed_propietario.id]
        )
        assert inmuebles == []

    async def test_should_return_403_when_relacion_is_pendiente_not_activa(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="pendiente",
        )

        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(propietario_id=str(seed_propietario.id)),
            files=[_fake_photo_file()],
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 403

    async def test_should_return_403_when_relacion_is_revocada(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="revocada",
        )

        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(propietario_id=str(seed_propietario.id)),
            files=[_fake_photo_file()],
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 403

    async def test_should_return_422_when_agente_omits_propietario_id(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
    ) -> None:
        # Arrange
        await _seed_agencia(db_session, miembro_id=seed_agente.id)

        # Act
        response = await client.post(
            "/inmuebles/",
            data=_valid_form_fields(),
            files=[_fake_photo_file()],
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /inmuebles/{id} como agente
# ---------------------------------------------------------------------------


class TestPutInmuebleAgenteSuccess:
    async def test_should_return_200_and_keep_original_agente_id_when_second_agente_edits(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        segundo_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: seed_agente published; segundo_agente is a member of the
        # same agencia, which has an activa relación with the propietario.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(
            segundo_agente.id, agencia.id
        )
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)

        # Act
        response = await client.put(
            f"/inmuebles/{inmueble.id}",
            json=_edit_payload(),
            headers=_agente_header(segundo_agente.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["direccion"] == "Carrera 50 # 10-20"
        assert body["agente_id"] == str(seed_agente.id)
        assert body["propietario_id"] == str(seed_propietario.id)


class TestPutInmuebleAgenteRejectedCases:
    async def test_should_return_403_when_agente_belongs_to_a_different_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        agente_otra_agencia: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        await _seed_agencia(db_session, miembro_id=agente_otra_agencia.id)
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)

        # Act
        response = await client.put(
            f"/inmuebles/{inmueble.id}",
            json=_edit_payload(),
            headers=_agente_header(agente_otra_agencia.id),
        )

        # Assert
        assert response.status_code == 403
        sin_cambios = await InmuebleRepositoryPostgres(db_session).obtener_por_id(
            inmueble.id  # type: ignore[arg-type]
        )
        assert sin_cambios is not None
        assert sin_cambios.direccion == "Calle 10 # 20-30"


# ---------------------------------------------------------------------------
# PATCH /inmuebles/{id}/disponibilidad como agente
# ---------------------------------------------------------------------------


class TestPatchDisponibilidadAgenteSuccess:
    async def test_should_return_200_and_change_estado_when_agencia_has_active_relacion(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)
        assert inmueble.estado == EstadoInmueble.DISPONIBLE

        # Act
        response = await client.patch(
            f"/inmuebles/{inmueble.id}/disponibilidad",
            json={"nuevo_estado": "oculto"},
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["estado"] == "oculto"


class TestPatchDisponibilidadAgenteRejectedCases:
    async def test_should_return_403_when_agencia_has_no_active_relacion(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        agente_otra_agencia: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        await _seed_agencia(db_session, miembro_id=agente_otra_agencia.id)
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)

        # Act
        response = await client.patch(
            f"/inmuebles/{inmueble.id}/disponibilidad",
            json={"nuevo_estado": "oculto"},
            headers=_agente_header(agente_otra_agencia.id),
        )

        # Assert
        assert response.status_code == 403
        sin_cambios = await InmuebleRepositoryPostgres(db_session).obtener_por_id(
            inmueble.id  # type: ignore[arg-type]
        )
        assert sin_cambios is not None
        assert sin_cambios.estado == EstadoInmueble.DISPONIBLE


# ---------------------------------------------------------------------------
# GET /inmuebles/gestionados
# ---------------------------------------------------------------------------


class TestGetInmueblesGestionados:
    async def test_should_return_only_inmuebles_of_propietarios_with_active_relacion(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
        otro_propietario: UsuarioORM,
    ) -> None:
        # Arrange: seed_agente's agencia has an activa relación with
        # seed_propietario and a revocada one with otro_propietario.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=seed_propietario.id,
            estado="activa",
        )
        await _seed_relacion(
            db_session,
            agencia_id=agencia.id,
            propietario_id=otro_propietario.id,
            estado="revocada",
        )
        gestionado = await _seed_inmueble(
            db_session,
            seed_propietario.id,
            agente_id=seed_agente.id,
            direccion="Calle 1 # 1-01",
        )
        no_gestionado = await _seed_inmueble(
            db_session,
            otro_propietario.id,
            agente_id=seed_agente.id,
            direccion="Calle 99 # 99-99",
        )

        # Act
        response = await client.get(
            "/inmuebles/gestionados", headers=_agente_header(seed_agente.id)
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        ids_devueltos = {item["id"] for item in body}
        assert str(gestionado.id) in ids_devueltos
        assert str(no_gestionado.id) not in ids_devueltos

    async def test_should_return_empty_list_when_agencia_has_no_active_relaciones(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
    ) -> None:
        # Arrange
        await _seed_agencia(db_session, miembro_id=seed_agente.id)

        # Act
        response = await client.get(
            "/inmuebles/gestionados", headers=_agente_header(seed_agente.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Regresión: los endpoints existentes de propietario (sin agente) siguen
# funcionando exactamente igual que en HU-001.
# ---------------------------------------------------------------------------


class TestPropietarioEndpointsRegression:
    async def test_propietario_post_put_and_patch_flow_is_unaffected_by_agente_support(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
        raw_s3_client: BaseClient,
        settings: Settings,
    ) -> None:
        # Arrange
        response_body: dict = {}

        try:
            # Act: POST, no propietario_id field at all (pure HU-001 shape).
            post_response = await client.post(
                "/inmuebles/",
                data=_valid_form_fields(),
                files=[_fake_photo_file()],
                headers=_propietario_header(seed_propietario.id),
            )

            # Assert: POST
            assert post_response.status_code == 201
            response_body = post_response.json()
            assert response_body["propietario_id"] == str(seed_propietario.id)
            assert response_body.get("agente_id") is None
            inmueble_id = response_body["id"]

            # Act: PUT
            put_response = await client.put(
                f"/inmuebles/{inmueble_id}",
                json=_edit_payload(),
                headers=_propietario_header(seed_propietario.id),
            )

            # Assert: PUT
            assert put_response.status_code == 200
            assert put_response.json()["direccion"] == "Carrera 50 # 10-20"

            # Act: PATCH
            patch_response = await client.patch(
                f"/inmuebles/{inmueble_id}/disponibilidad",
                json={"nuevo_estado": "oculto"},
                headers=_propietario_header(seed_propietario.id),
            )

            # Assert: PATCH
            assert patch_response.status_code == 200
            assert patch_response.json()["estado"] == "oculto"
        finally:
            _delete_fotos_from_minio(raw_s3_client, settings, response_body)
