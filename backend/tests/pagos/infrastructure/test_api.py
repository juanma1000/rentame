"""Integration tests for the `pagos` API layer (group 7 of
`openspec/changes/pago-mensual-renta/tasks.md`), covering every scenario
of `openspec/changes/pago-mensual-renta/specs/pagos/spec.md` end-to-end
through real HTTP requests against the real FastAPI app (`main.app`), a
real PostgreSQL test database (`db_session`/`seed_inquilino` from
`backend/tests/conftest.py`) — no mocks, following the precedent of
`tests/firma_contrato/infrastructure/test_api.py`.

TDD Red phase: `main.py` registers no router for the `pagos` domain yet,
and neither `pagos/infrastructure/api/router.py` nor `schemas.py` exist.
Every request is therefore expected to fail with FastAPI's default 404
(no matching route). This file fixes, by construction, the exact contract
`backend-expert` must implement (tasks 7.2/7.4/7.6):

- `POST /pagos/{pago_id}/iniciar` — requires
  `Authorization: Bearer <JWT inquilino>`. `200` with `{"id", "estado",
  "referencia_externa", ...}` for a `pendiente` pago (`FakeAdapter` always
  completes). `404` for a pago inexistente. `409` for a pago ya
  `completado`.
- `POST /pagos/webhook` — JSON body: `referencia_externa`, `estado`
  (`"completado"`/`"fallido"`). No auth required (called by the pasarela
  externa). `completado` sets `fecha_pago`; `fallido` does not.
- `GET /arrendamientos/{arrendamiento_activo_id}/pagos` — historial
  completo, sin filtrar por estado.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from firma_contrato.infrastructure.persistence.models import ArrendamientoActivoORM, ContratoORM
from inmuebles.infrastructure.persistence.models import InmuebleORM
from main import app
from pagos.domain.pago import Pago
from pagos.infrastructure.persistence.repository import PagoRepositoryPostgres
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


async def _seed_arrendamiento_activo(
    db_session: AsyncSession, usuario_id: uuid.UUID, *, valor_mensual: str = "1800000"
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert a real póliza -> contrato -> arrendamiento_activo -> inmueble
    chain, returning `(arrendamiento_activo_id, propietario_id)`."""
    propietario = UsuarioORM(
        id=uuid.uuid4(),
        email=f"propietario-{uuid.uuid4()}@example.com",
        rol="propietario",
    )
    db_session.add(propietario)
    await db_session.flush()

    inmueble = InmuebleORM(
        id=uuid.uuid4(),
        propietario_id=propietario.id,
        direccion="Calle 10 # 20-30",
        barrio="Centro",
        ciudad="Cali",
        tipo="apartamento",
        area_m2=Decimal("60.0"),
        habitaciones=2,
        banos=1,
        valor_mensual=Decimal(valor_mensual),
        descripcion="Apartamento de prueba",
        estado="no_disponible",
    )
    db_session.add(inmueble)
    await db_session.flush()

    poliza = PolizaArrendamientoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        estado="aprobada",
        fecha=datetime.now(UTC),
        prima_mensual=Decimal("50000.00"),
    )
    db_session.add(poliza)
    await db_session.flush()

    contrato = ContratoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        poliza_id=poliza.id,
        inmueble_id=inmueble.id,
        estado="firmado",
        documento_referencia="contrato-texto-generado",
        fecha=datetime.now(UTC),
    )
    db_session.add(contrato)
    await db_session.flush()

    arrendamiento = ArrendamientoActivoORM(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        poliza_id=poliza.id,
        contrato_id=contrato.id,
        inmueble_id=inmueble.id,
        estado="activo",
        fecha_inicio=date.today(),
    )
    db_session.add(arrendamiento)
    await db_session.flush()

    return arrendamiento.id, propietario.id


async def _seed_pago_pendiente(
    db_session: AsyncSession, arrendamiento_activo_id: uuid.UUID, *, monto: float = 1_800_000.0
) -> uuid.UUID:
    repository = PagoRepositoryPostgres(db_session)
    pago = Pago.crear(
        arrendamiento_activo_id=arrendamiento_activo_id,
        monto=monto,
        fecha_limite=date.today() + timedelta(days=5),
    )
    guardado = await repository.guardar(pago)
    return guardado.id


class TestIniciarPagoEndpoint:
    async def test_should_return_200_for_pago_pendiente(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        arrendamiento_id, _ = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago_id = await _seed_pago_pendiente(db_session, arrendamiento_id)

        # Act
        response = await client.post(
            f"/pagos/{pago_id}/iniciar",
            headers=_auth_header(seed_inquilino.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(pago_id)
        assert body["estado"] == "completado"
        assert body["referencia_externa"]

    async def test_should_return_404_when_pago_does_not_exist(
        self, client: httpx.AsyncClient, seed_inquilino: UsuarioORM
    ) -> None:
        # Act
        response = await client.post(
            f"/pagos/{uuid.uuid4()}/iniciar",
            headers=_auth_header(seed_inquilino.id),
        )

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_should_return_409_when_pago_already_completado(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        arrendamiento_id, _ = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago_id = await _seed_pago_pendiente(db_session, arrendamiento_id)
        primera = await client.post(
            f"/pagos/{pago_id}/iniciar",
            headers=_auth_header(seed_inquilino.id),
        )
        assert primera.status_code == 200

        # Act
        response = await client.post(
            f"/pagos/{pago_id}/iniciar",
            headers=_auth_header(seed_inquilino.id),
        )

        # Assert
        assert response.status_code == 409
        assert "detail" in response.json()

    async def test_should_return_401_when_no_token(self, client: httpx.AsyncClient) -> None:
        # Act
        response = await client.post(f"/pagos/{uuid.uuid4()}/iniciar")

        # Assert
        assert response.status_code == 401


class TestWebhookPagoEndpoint:
    async def test_completado_sets_fecha_pago(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange: use a slow (async) pasarela flow — record referencia via a
        # pending-Wompi-style webhook — but with FakeAdapter (always
        # completado synchronously), so simulate a fresh referencia_externa
        # via the repository directly to exercise the webhook in isolation.
        arrendamiento_id, _ = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago_id = await _seed_pago_pendiente(db_session, arrendamiento_id)
        repository = PagoRepositoryPostgres(db_session)
        pago = await repository.obtener_por_id(pago_id)
        assert pago is not None
        pago.registrar_intento(referencia_externa="ext-webhook-1")
        await repository.actualizar(pago)

        # Act
        response = await client.post(
            "/pagos/webhook",
            json={"referencia_externa": "ext-webhook-1", "estado": "completado"},
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "completado"
        assert body["fecha_pago"] is not None

    async def test_fallido_does_not_set_fecha_pago(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        arrendamiento_id, _ = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pago_id = await _seed_pago_pendiente(db_session, arrendamiento_id)
        repository = PagoRepositoryPostgres(db_session)
        pago = await repository.obtener_por_id(pago_id)
        assert pago is not None
        pago.registrar_intento(referencia_externa="ext-webhook-2")
        await repository.actualizar(pago)

        # Act
        response = await client.post(
            "/pagos/webhook",
            json={"referencia_externa": "ext-webhook-2", "estado": "fallido"},
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "fallido"
        assert body["fecha_pago"] is None

    async def test_returns_404_when_referencia_externa_not_found(
        self, client: httpx.AsyncClient
    ) -> None:
        # Act
        response = await client.post(
            "/pagos/webhook",
            json={"referencia_externa": "no-existe", "estado": "completado"},
        )

        # Assert
        assert response.status_code == 404


class TestHistorialPagosEndpoint:
    async def test_returns_every_pago_regardless_of_estado(
        self,
        client: httpx.AsyncClient,
        seed_inquilino: UsuarioORM,
        db_session: AsyncSession,
    ) -> None:
        # Arrange
        arrendamiento_id, _ = await _seed_arrendamiento_activo(db_session, seed_inquilino.id)
        pendiente_id = await _seed_pago_pendiente(db_session, arrendamiento_id)
        completado_id = await _seed_pago_pendiente(db_session, arrendamiento_id, monto=900_000.0)
        await client.post(
            f"/pagos/{completado_id}/iniciar",
            headers=_auth_header(seed_inquilino.id),
        )

        # Act
        response = await client.get(
            f"/arrendamientos/{arrendamiento_id}/pagos",
            headers=_auth_header(seed_inquilino.id),
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        ids = {p["id"] for p in body["pagos"]}
        assert ids == {str(pendiente_id), str(completado_id)}
        estados = {p["estado"] for p in body["pagos"]}
        assert estados == {"pendiente", "completado"}
