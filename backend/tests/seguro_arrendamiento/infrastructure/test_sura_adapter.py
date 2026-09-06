"""Unit tests for `SuraAdapter`
(`seguro_arrendamiento/infrastructure/adapters/sura_adapter.py`).

Covers task 6.1 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`: the real Sura
API is never called in CI — every test injects an `httpx.AsyncClient` built
with `httpx.MockTransport`, so responses (including a timeout) are fully
controlled here. Sura's exact contract is an open question in design.md,
resolved here with the smallest reasonable shape (`POST {base_url}/polizas`,
multipart body, `Sura-API-Key` header, JSON response with
`estado`/`prima_mensual`/`vigencia_desde`/`vigencia_hasta`/`referencia`) —
adjust this adapter, not the domain port, once Sura's real contract is
confirmed, same precedent as `identidad.infrastructure.adapters.
truora_adapter.TruoraAdapter`.

TDD Red phase:
`seguro_arrendamiento/infrastructure/adapters/sura_adapter.py` does not
exist yet, so this test is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 6.2).
"""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from seguro_arrendamiento.domain.exceptions import ContratacionNoDisponible
from seguro_arrendamiento.infrastructure.adapters.sura_adapter import SuraAdapter


def _client_with(handler) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


class TestSuraAdapterAprobada:
    async def test_should_return_aprobada_true_when_sura_responds_aprobada(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Sura-API-Key"] == "test-api-key"
            return httpx.Response(
                200,
                json={
                    "estado": "aprobada",
                    "prima_mensual": 45000.0,
                    "vigencia_desde": "2026-01-01",
                    "vigencia_hasta": "2027-01-01",
                    "referencia": "sura-poliza-1",
                },
            )

        adapter = SuraAdapter(
            api_key="test-api-key",
            base_url="https://api.sura.test",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.contratar(cedula="1002003004", documentos=[b"doc1", b"doc2"])

        # Assert
        assert resultado.aprobada is True
        assert resultado.referencia_externa == "sura-poliza-1"
        assert resultado.prima_mensual == 45000.0
        assert resultado.vigencia_desde == date(2026, 1, 1)
        assert resultado.vigencia_hasta == date(2027, 1, 1)


class TestSuraAdapterRechazada:
    async def test_should_return_aprobada_false_when_sura_responds_non_aprobada_estado(
        self,
    ) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"estado": "rechazada", "referencia": "sura-poliza-2"})

        adapter = SuraAdapter(
            api_key="test-api-key",
            base_url="https://api.sura.test",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.contratar(cedula="1002003004", documentos=[b"doc"])

        # Assert
        assert resultado.aprobada is False
        assert resultado.referencia_externa == "sura-poliza-2"
        assert resultado.prima_mensual is None


class TestSuraAdapterNoDisponible:
    async def test_should_raise_contratacion_no_disponible_on_timeout(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        adapter = SuraAdapter(
            api_key="test-api-key",
            base_url="https://api.sura.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ContratacionNoDisponible):
            await adapter.contratar(cedula="1002003004", documentos=[b"doc"])

    async def test_should_raise_contratacion_no_disponible_on_connect_error(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        adapter = SuraAdapter(
            api_key="test-api-key",
            base_url="https://api.sura.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ContratacionNoDisponible):
            await adapter.contratar(cedula="1002003004", documentos=[b"doc"])

    async def test_should_raise_contratacion_no_disponible_on_5xx_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "service unavailable"})

        adapter = SuraAdapter(
            api_key="test-api-key",
            base_url="https://api.sura.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ContratacionNoDisponible):
            await adapter.contratar(cedula="1002003004", documentos=[b"doc"])
