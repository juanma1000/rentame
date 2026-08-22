"""Integration tests for the `agencias` API layer (group 7 of
`openspec/changes/hu-007/tasks.md`), covering every scenario of
`openspec/changes/hu-007/specs/agencias/spec.md` plus the despublicación
cascade scenarios of `openspec/changes/hu-007/specs/inmuebles/spec.md`,
end-to-end through real HTTP requests against the real FastAPI app
(`main.app`), a real PostgreSQL test database (`rentame_test`, via
`db_session`/`seed_agente`/`seed_propietario` from
`backend/tests/conftest.py`) — no mocks anywhere, following the precedent
of `tests/inmuebles/infrastructure/test_api.py`.

TDD Red phase: none of the endpoints below exist yet — `main.py` registers
no router for the `agencias` domain, and neither
`agencias/infrastructure/api/router.py` nor
`agencias/infrastructure/api/schemas.py` exist. Every request is therefore
expected to fail with FastAPI's default 404 (no matching route) today, not
with an import/collection error, since this file only imports `main.app`
plus already-existing collaborators (the domain entities, the real
Postgres-backed repositories of `agencias`/`inmuebles`, and the JWT test
helper). This file fixes, by construction, the exact contract
`backend-expert` must implement:

- `POST /agencias/` — JSON body `{"razon_social": str, "nit": str}`.
  Requires `Authorization: Bearer <JWT agente>`. `201` with an
  `AgenciaResponse` (`{"id", "razon_social", "nit"}`) when the agente does
  not yet belong to an agencia (the creating agente becomes its first
  member — verified indirectly via `POST /agencias/{id}/relaciones` +
  `confirmar` needing that membership, and directly by asserting a second
  `POST /agencias/` by the same agente is rejected). `409` (domain
  `AgenteYaTieneAgencia`) when the agente already belongs to one.

- `POST /agencias/{agencia_id}/solicitudes` — no body. Requires
  `Authorization: Bearer <JWT agente>` (the agente sin agencia
  requesting to join). `201` with a `SolicitudIngresoResponse`
  (`{"id", "agencia_id", "agente_id", "estado": "pendiente"}`).

- `POST /agencias/solicitudes/{solicitud_id}/aprobar` — no body. Requires
  `Authorization: Bearer <JWT agente>` (must already be a member of the
  solicitud's agencia). `200` with the same shape, `"estado": "aprobada"`,
  and the solicitante becomes a member (verified via a follow-up action
  that requires membership). `403` (`AgenteNoEsMiembroDeAgencia`) when the
  approver is not a member of that agencia.

- `POST /agencias/salir` — no body. Requires
  `Authorization: Bearer <JWT agente>` (must belong to an agencia). `204`
  on success. `409` (`UltimoAgenteConRelacionesActivas`) when the caller is
  the last member of an agencia that still has an `activa` relación.

- `POST /agencias/{agencia_id}/relaciones` — no body. Requires
  `Authorization: Bearer <JWT propietario>`. `201` with a `RelacionResponse`
  (`{"id", "agencia_id", "propietario_id", "estado": "pendiente",
  "agente_responsable_id": null}`).

- `POST /agencias/relaciones/{relacion_id}/confirmar` — no body. Requires
  `Authorization: Bearer <JWT agente>` (must be a member of the relación's
  agencia). `200` with the same shape, `"estado": "activa"`. Auto-revokes
  any previous `activa` relación of the same propietario and runs the real
  despublicación cascade (verified against real Postgres state of a seeded
  `Inmueble`). `403` (`AgenteNoEsMiembroDeAgencia`) when the confirming
  agente is not a member.

- `POST /agencias/relaciones/{relacion_id}/revocar` — no body. Requires
  `Authorization: Bearer <JWT propietario>` (no agencia-side approval —
  any propietario can revoke their own relación per spec.md, but only
  their own). `200` with the same shape, `"estado": "revocada"`, running
  the real despublicación cascade. `403`
  (`agencias.domain.exceptions.PropietarioInvalido`) when the caller is
  not the relación's own propietario — no mutation, no cascade.

- `PATCH /agencias/relaciones/{relacion_id}/responsable` — JSON body
  `{"nuevo_agente_id": "<uuid>"}`. Requires
  `Authorization: Bearer <JWT agente>` (must be a member of the relación's
  agencia). `200` with the updated `RelacionResponse`
  (`agente_responsable_id` updated, `estado` untouched). `403`
  (`AgenteNoEsMiembroDeAgencia`) when the caller (`solicitante_id`) is not
  a member of the relación's agencia, or when `nuevo_agente_id` is not a
  member of that same agencia.

- `GET /agencias/mia/propietarios` — no body. Requires
  `Authorization: Bearer <JWT agente>` (must belong to an agencia). `200`
  with a JSON array, one item per `RelacionAgenciaPropietario` of the
  caller's agencia: `{"id", "propietario_id", "estado",
  "agente_responsable_id"}`.

All rejection status codes above (`403`/`404`/`409`) are `backend-expert`'s
to wire via new `@app.exception_handler(...)` registrations in `main.py`,
mapping `agencias.domain.exceptions.{AgenteYaTieneAgencia,
SolicitudNoEncontrada, RelacionNoEncontrada, AgenteNoEsMiembroDeAgencia,
UltimoAgenteConRelacionesActivas}` — body shape `{"detail": "<message>"}`,
same convention as the `inmuebles` handlers.

Every test that persists an `Agencia`/`SolicitudIngreso`/
`RelacionAgenciaPropietario`/`Inmueble` relies on `db_session`'s per-test
rollback (see `backend/tests/conftest.py`) for Postgres cleanup — the
`client` fixture below overrides `get_db_session` with that same session
instance so every request in a test shares one transaction, exactly like
`tests/inmuebles/infrastructure/test_api.py` already does. `Inmueble`
fixtures needing a non-null `agente_id` are built via the real
`Inmueble.crear` factory and then have `agente_id` stamped directly on the
instance before insertion through `InmuebleRepositoryPostgres` — the same
gap/workaround already documented and used by
`tests/agencias/application/test_confirmar_relacion.py`, since the public
`inmuebles` HTTP API (HU-001) does not accept `agente_id` yet (HU-002).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import (
    RelacionAgenciaPropietario,
)
from agencias.domain.solicitud_ingreso import SolicitudIngreso
from agencias.infrastructure.persistence.repository import (
    AgenciaRepositoryPostgres,
    RelacionRepositoryPostgres,
    SolicitudIngresoRepositoryPostgres,
    UsuarioAgenciaRepositoryPostgres,
)
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from main import app
from shared.infrastructure.database import get_db_session
from tests.utils.auth import build_valid_token
from usuarios.infrastructure.persistence.models import UsuarioORM

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


@pytest_asyncio.fixture
async def otro_agente(db_session: AsyncSession) -> UsuarioORM:
    """A second "agente" user, distinct from `seed_agente`."""
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"otro-agente-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


@pytest_asyncio.fixture
async def tercer_agente(db_session: AsyncSession) -> UsuarioORM:
    """A third "agente" user, distinct from `seed_agente`/`otro_agente`."""
    usuario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"tercer-agente-{uuid.uuid4()}@example.com",
        rol="agente",
    )
    db_session.add(usuario)
    await db_session.flush()
    return usuario


def _agente_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "agente")
    return {"Authorization": f"Bearer {token}"}


def _propietario_header(usuario_id: uuid.UUID) -> dict[str, str]:
    token = build_valid_token(str(usuario_id), "propietario")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test data builders — direct repository access (agencias + inmuebles)
# ---------------------------------------------------------------------------


async def _seed_agencia(
    db_session: AsyncSession, *, miembro_id: uuid.UUID | None = None
) -> Agencia:
    """Persist an `Agencia` via the real repository, optionally linking
    `miembro_id` (`usuario.agencia_id`) as its first member."""
    repository = AgenciaRepositoryPostgres(db_session)
    agencia = await repository.guardar(Agencia.crear(razon_social="Agencia Test", nit="900123456"))
    if miembro_id is not None:
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(miembro_id, agencia.id)
    await db_session.flush()
    return agencia


async def _seed_solicitud(
    db_session: AsyncSession, *, agencia_id: uuid.UUID, agente_id: uuid.UUID
) -> SolicitudIngreso:
    repository = SolicitudIngresoRepositoryPostgres(db_session)
    solicitud = await repository.guardar(
        SolicitudIngreso.crear(agencia_id=agencia_id, agente_id=agente_id)
    )
    await db_session.flush()
    return solicitud


async def _seed_relacion(
    db_session: AsyncSession,
    *,
    agencia_id: uuid.UUID,
    propietario_id: uuid.UUID,
    activa: bool = False,
) -> RelacionAgenciaPropietario:
    repository = RelacionRepositoryPostgres(db_session)
    relacion = await repository.guardar(
        RelacionAgenciaPropietario.crear(agencia_id=agencia_id, propietario_id=propietario_id)
    )
    if activa:
        relacion.activar()
        relacion = await repository.actualizar(relacion)
    await db_session.flush()
    return relacion


def _build_inmueble(propietario_id: uuid.UUID, *, agente_id: uuid.UUID | None = None) -> Inmueble:
    """Build an `Inmueble` via the real domain factory, stamping `agente_id`
    on the resulting instance afterwards (`Inmueble.crear` does not accept
    `agente_id` yet — HU-002 gap, see module docstring)."""
    inmueble = Inmueble.crear(
        propietario_id=propietario_id,
        direccion="Calle 10 # 20-30",
        barrio="El Poblado",
        ciudad="Medellin",
        tipo="apartamento",
        area_m2=Decimal("65.5"),
        habitaciones=2,
        banos=2,
        valor_mensual=Decimal("1500000"),
        descripcion="Apartamento amoblado",
        fotos=[
            FotoInmueble(
                url_storage="https://storage.example.com/inmuebles/fotos/1.jpg",
                storage_key="inmuebles/fotos/1.jpg",
                orden=1,
                es_principal=True,
            )
        ],
    )
    inmueble.agente_id = agente_id  # type: ignore[attr-defined]
    return inmueble


async def _seed_inmueble(
    db_session: AsyncSession, propietario_id: uuid.UUID, *, agente_id: uuid.UUID | None = None
) -> Inmueble:
    repository = InmuebleRepositoryPostgres(db_session)
    inmueble = _build_inmueble(propietario_id, agente_id=agente_id)
    guardado = await repository.guardar(inmueble)
    await db_session.flush()
    return guardado


async def _refrescar_inmueble(db_session: AsyncSession, inmueble_id: uuid.UUID) -> Inmueble:
    repository = InmuebleRepositoryPostgres(db_session)
    inmueble = await repository.obtener_por_id(inmueble_id)
    assert inmueble is not None
    return inmueble


# ---------------------------------------------------------------------------
# POST /agencias/
# ---------------------------------------------------------------------------


class TestPostAgenciasSuccess:
    async def test_should_return_201_and_link_creating_agente_as_first_member(
        self, client: httpx.AsyncClient, seed_agente: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            "/agencias/",
            json={"razon_social": "Inmobiliaria del Valle", "nit": "900123456"},
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["razon_social"] == "Inmobiliaria del Valle"
        assert body["nit"] == "900123456"


class TestPostAgenciasRejectedCases:
    async def test_should_return_409_when_agente_already_belongs_to_an_agencia(
        self, client: httpx.AsyncClient, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        await _seed_agencia(db_session, miembro_id=seed_agente.id)

        # Act
        response = await client.post(
            "/agencias/",
            json={"razon_social": "Otra Inmobiliaria", "nit": "900999999"},
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 409

    async def test_should_return_401_when_authorization_header_is_missing(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/agencias/", json={"razon_social": "Inmobiliaria del Valle", "nit": "900123456"}
        )

        # Assert
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /agencias/{id}/solicitudes and POST /agencias/solicitudes/{id}/aprobar
# ---------------------------------------------------------------------------


class TestSolicitarYAprobarIngreso:
    async def test_should_return_201_with_pendiente_solicitud_when_agente_sin_agencia_requests(
        self, client: httpx.AsyncClient, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)

        # Act
        response = await client.post(
            f"/agencias/{agencia.id}/solicitudes",
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["agencia_id"] == str(agencia.id)
        assert body["agente_id"] == str(seed_agente.id)
        assert body["estado"] == "pendiente"

    async def test_should_return_200_and_link_solicitante_when_a_member_aprueba(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
    ) -> None:
        # Arrange: seed_agente is the sole existing member; otro_agente requested to join.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        solicitud = await _seed_solicitud(
            db_session, agencia_id=agencia.id, agente_id=otro_agente.id
        )

        # Act
        response = await client.post(
            f"/agencias/solicitudes/{solicitud.id}/aprobar",
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "aprobada"

        # Assert (membership effect, verified via real DB state)
        membresia = await UsuarioAgenciaRepositoryPostgres(db_session).obtener_agencia_id(
            otro_agente.id
        )
        assert membresia == agencia.id

    async def test_should_return_403_when_approver_is_not_a_member_of_that_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
    ) -> None:
        # Arrange: otro_agente requests to join agencia, but seed_agente never joined it.
        agencia = await _seed_agencia(db_session)
        solicitud = await _seed_solicitud(
            db_session, agencia_id=agencia.id, agente_id=otro_agente.id
        )

        # Act
        response = await client.post(
            f"/agencias/solicitudes/{solicitud.id}/aprobar",
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /agencias/salir
# ---------------------------------------------------------------------------


class TestPostAgenciasSalir:
    async def test_should_return_204_when_agencia_has_more_than_one_member(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(
            otro_agente.id, agencia.id
        )

        # Act
        response = await client.post("/agencias/salir", headers=_agente_header(seed_agente.id))

        # Assert
        assert response.status_code == 204
        membresia = await UsuarioAgenciaRepositoryPostgres(db_session).obtener_agencia_id(
            seed_agente.id
        )
        assert membresia is None

    async def test_should_return_409_when_last_member_has_active_relaciones(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )

        # Act
        response = await client.post("/agencias/salir", headers=_agente_header(seed_agente.id))

        # Assert
        assert response.status_code == 409
        membresia = await UsuarioAgenciaRepositoryPostgres(db_session).obtener_agencia_id(
            seed_agente.id
        )
        assert membresia == agencia.id


# ---------------------------------------------------------------------------
# POST /agencias/{id}/relaciones
# ---------------------------------------------------------------------------


class TestPostAgenciasRelaciones:
    async def test_should_return_201_with_pendiente_relacion_when_propietario_inicia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)

        # Act
        response = await client.post(
            f"/agencias/{agencia.id}/relaciones",
            headers=_propietario_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["agencia_id"] == str(agencia.id)
        assert body["propietario_id"] == str(seed_propietario.id)
        assert body["estado"] == "pendiente"
        assert body["agente_responsable_id"] is None

    async def test_should_return_401_when_authorization_header_is_missing(
        self, client: httpx.AsyncClient, db_session: AsyncSession
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)

        # Act
        response = await client.post(f"/agencias/{agencia.id}/relaciones")

        # Assert
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /agencias/relaciones/{id}/confirmar
# ---------------------------------------------------------------------------


class TestPostRelacionesConfirmar:
    async def test_should_return_200_with_activa_relacion_when_a_member_confirms(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id
        )

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/confirmar",
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["estado"] == "activa"

    async def test_should_return_403_when_confirming_agente_is_not_a_member(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        otro_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id
        )

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/confirmar",
            headers=_agente_header(otro_agente.id),
        )

        # Assert
        assert response.status_code == 403

    async def test_should_revoke_previous_activa_relacion_and_despublicar_its_inmuebles(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        """Confirming a new relación (Agencia B) auto-revokes the propietario's
        previous `activa` relación (Agencia A) and hides every `Inmueble`
        managed by an agente of Agencia A — the real cascade, verified
        against real Postgres state (spec.md "Contratar una agencia nueva
        revoca la anterior" + inmuebles spec.md cascade scenario)."""
        # Arrange: Agencia A (seed_agente) already active with the propietario,
        # managing one of their inmuebles.
        agencia_a = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await _seed_relacion(
            db_session, agencia_id=agencia_a.id, propietario_id=seed_propietario.id, activa=True
        )
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)
        assert inmueble.estado == EstadoInmueble.DISPONIBLE

        # Arrange: Agencia B (otro_agente), pendiente relación with the same propietario.
        agencia_b = await _seed_agencia(db_session, miembro_id=otro_agente.id)
        relacion_b = await _seed_relacion(
            db_session, agencia_id=agencia_b.id, propietario_id=seed_propietario.id
        )

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion_b.id}/confirmar",
            headers=_agente_header(otro_agente.id),
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["estado"] == "activa"

        inmueble_actualizado = await _refrescar_inmueble(db_session, inmueble.id)  # type: ignore[arg-type]
        assert inmueble_actualizado.estado == EstadoInmueble.OCULTO


# ---------------------------------------------------------------------------
# POST /agencias/relaciones/{id}/revocar
# ---------------------------------------------------------------------------


class TestPostRelacionesRevocar:
    async def test_should_return_200_with_revocada_relacion_when_propietario_revokes(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/revocar",
            headers=_propietario_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["estado"] == "revocada"

    async def test_should_despublicar_inmuebles_managed_by_the_revoked_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )
        inmueble = await _seed_inmueble(db_session, seed_propietario.id, agente_id=seed_agente.id)
        assert inmueble.estado == EstadoInmueble.DISPONIBLE

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/revocar",
            headers=_propietario_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 200
        inmueble_actualizado = await _refrescar_inmueble(db_session, inmueble.id)  # type: ignore[arg-type]
        assert inmueble_actualizado.estado == EstadoInmueble.OCULTO

    async def test_should_not_affect_inmuebles_published_directly_without_agente(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )
        inmueble_sin_agente = await _seed_inmueble(db_session, seed_propietario.id, agente_id=None)
        assert inmueble_sin_agente.estado == EstadoInmueble.DISPONIBLE

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/revocar",
            headers=_propietario_header(seed_propietario.id),
        )

        # Assert
        assert response.status_code == 200
        inmueble_actualizado = await _refrescar_inmueble(
            db_session, inmueble_sin_agente.id  # type: ignore[arg-type]
        )
        assert inmueble_actualizado.estado == EstadoInmueble.DISPONIBLE

    async def test_should_return_403_when_caller_is_not_the_relacion_owner(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: relación belongs to `seed_propietario`, but a different
        # propietario attempts to revoke it.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )
        otro_propietario_id = uuid.uuid4()
        db_session.add(
            UsuarioORM(
                id=otro_propietario_id,
                email=f"otro-propietario-{uuid.uuid4()}@example.com",
                rol="propietario",
            )
        )
        await db_session.flush()

        # Act
        response = await client.post(
            f"/agencias/relaciones/{relacion.id}/revocar",
            headers=_propietario_header(otro_propietario_id),
        )

        # Assert: rejected, and the relación is untouched.
        assert response.status_code == 403
        relacion_sin_cambios = await RelacionRepositoryPostgres(db_session).obtener_por_id(
            relacion.id  # type: ignore[arg-type]
        )
        assert relacion_sin_cambios is not None
        assert relacion_sin_cambios.estado.value == "activa"


# ---------------------------------------------------------------------------
# PATCH /agencias/relaciones/{id}/responsable
# ---------------------------------------------------------------------------


class TestPatchRelacionesResponsable:
    async def test_should_return_200_and_update_agente_responsable_when_new_one_is_a_member(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(
            otro_agente.id, agencia.id
        )
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )

        # Act
        response = await client.patch(
            f"/agencias/relaciones/{relacion.id}/responsable",
            json={"nuevo_agente_id": str(otro_agente.id)},
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["agente_responsable_id"] == str(otro_agente.id)
        assert body["estado"] == "activa"

    async def test_should_return_403_when_nuevo_agente_is_not_a_member_of_the_same_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: otro_agente belongs to no agencia (or a different one).
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )

        # Act
        response = await client.patch(
            f"/agencias/relaciones/{relacion.id}/responsable",
            json={"nuevo_agente_id": str(otro_agente.id)},
            headers=_agente_header(seed_agente.id),
        )

        # Assert
        assert response.status_code == 403

    async def test_should_return_403_when_solicitante_is_not_a_member_of_the_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
        tercer_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: the relación belongs to `seed_agente`'s agencia, but the
        # caller (`otro_agente`) belongs to a different one and tries to
        # reassign the responsable to `tercer_agente`, a legitimate member.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        await UsuarioAgenciaRepositoryPostgres(db_session).asignar_agencia(
            tercer_agente.id, agencia.id
        )
        otra_agencia = await _seed_agencia(db_session, miembro_id=otro_agente.id)
        relacion = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )

        # Act
        response = await client.patch(
            f"/agencias/relaciones/{relacion.id}/responsable",
            json={"nuevo_agente_id": str(tercer_agente.id)},
            headers=_agente_header(otro_agente.id),
        )

        # Assert: rejected, and `agente_responsable_id` is untouched.
        assert response.status_code == 403
        assert otra_agencia.id is not None  # otro_agente does belong to an agencia
        relacion_sin_cambios = await RelacionRepositoryPostgres(db_session).obtener_por_id(
            relacion.id  # type: ignore[arg-type]
        )
        assert relacion_sin_cambios is not None
        assert relacion_sin_cambios.agente_responsable_id is None


# ---------------------------------------------------------------------------
# GET /agencias/mia/propietarios
# ---------------------------------------------------------------------------


class TestGetMiaPropietarios:
    async def test_should_return_every_relacion_of_the_authenticated_agente_agencia(
        self,
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        seed_agente: UsuarioORM,
        otro_agente: UsuarioORM,
        seed_propietario: UsuarioORM,
    ) -> None:
        # Arrange: seed_agente's agencia has two relaciones; a second agencia
        # (otro_agente) has one, which must NOT show up.
        agencia = await _seed_agencia(db_session, miembro_id=seed_agente.id)
        relacion_activa = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=seed_propietario.id, activa=True
        )
        otro_propietario_id = uuid.uuid4()
        usuario = UsuarioORM(
            id=otro_propietario_id, email=f"p-{uuid.uuid4()}@example.com", rol="propietario"
        )
        db_session.add(usuario)
        await db_session.flush()
        relacion_pendiente = await _seed_relacion(
            db_session, agencia_id=agencia.id, propietario_id=otro_propietario_id
        )

        otra_agencia = await _seed_agencia(db_session, miembro_id=otro_agente.id)
        await _seed_relacion(
            db_session, agencia_id=otra_agencia.id, propietario_id=seed_propietario.id
        )

        # Act
        response = await client.get(
            "/agencias/mia/propietarios", headers=_agente_header(seed_agente.id)
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        ids_devueltos = {item["id"] for item in body}
        assert ids_devueltos == {str(relacion_activa.id), str(relacion_pendiente.id)}

    async def test_should_return_empty_list_when_agencia_has_no_relaciones(
        self, client: httpx.AsyncClient, db_session: AsyncSession, seed_agente: UsuarioORM
    ) -> None:
        # Arrange
        await _seed_agencia(db_session, miembro_id=seed_agente.id)

        # Act
        response = await client.get(
            "/agencias/mia/propietarios", headers=_agente_header(seed_agente.id)
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == []
