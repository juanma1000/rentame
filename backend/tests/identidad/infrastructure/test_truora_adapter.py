"""Unit tests for `TruoraAdapter`
(`identidad/infrastructure/adapters/truora_adapter.py`).

Covers task 6.1 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`: the real
Truora API is never called in CI — every test injects an `httpx.AsyncClient`
built with `httpx.MockTransport`, so responses (including a timeout) are
fully controlled here. This file fixes, by construction, the contract
`backend-expert` must satisfy (task 6.2):

- `TruoraAdapter(api_key: str, base_url: str, client: httpx.AsyncClient | None = None)`.
- `.validar(cedula=..., imagen_frente=..., imagen_dorso=...)` POSTs to
  `f"{base_url}/checks"` (multipart: `national_id`, `document_front`,
  `document_back`, header `Truora-API-Key: <api_key>`) and maps the JSON
  response's `"status"` field: `"success"` -> `ResultadoValidacion(aprobado=True, ...)`,
  anything else -> `aprobado=False`. `"check_id"` becomes
  `referencia_externa`.
- A network error, timeout, or a non-2xx response never raises an
  unhandled exception nor lets a 500 reach the caller — it raises
  `identidad.domain.exceptions.ValidacionNoDisponible` instead (mapped by
  the API layer to an explicit "validación no disponible" response).

TDD Red phase: `identidad/infrastructure/adapters/truora_adapter.py` does
not exist yet, so this test is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 6.2).
"""

from __future__ import annotations

import httpx
import pytest

from identidad.domain.exceptions import ValidacionNoDisponible
from identidad.infrastructure.adapters.truora_adapter import TruoraAdapter


def _client_with(handler) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


class TestTruoraAdapterAprobado:
    async def test_should_return_aprobado_true_when_truora_responds_success(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Truora-API-Key"] == "test-api-key"
            return httpx.Response(200, json={"status": "success", "check_id": "truora-check-1"})

        adapter = TruoraAdapter(
            api_key="test-api-key",
            base_url="https://api.truora.test",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.validar(
            cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )

        # Assert
        assert resultado.aprobado is True
        assert resultado.referencia_externa == "truora-check-1"


class TestTruoraAdapterRechazado:
    async def test_should_return_aprobado_false_when_truora_responds_non_success_status(
        self,
    ) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"status": "rejected", "check_id": "truora-check-2"})

        adapter = TruoraAdapter(
            api_key="test-api-key",
            base_url="https://api.truora.test",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.validar(
            cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )

        # Assert
        assert resultado.aprobado is False
        assert resultado.referencia_externa == "truora-check-2"


class TestTruoraAdapterNoDisponible:
    async def test_should_raise_validacion_no_disponible_on_timeout(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        adapter = TruoraAdapter(
            api_key="test-api-key",
            base_url="https://api.truora.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ValidacionNoDisponible):
            await adapter.validar(cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso")

    async def test_should_raise_validacion_no_disponible_on_connect_error(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        adapter = TruoraAdapter(
            api_key="test-api-key",
            base_url="https://api.truora.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ValidacionNoDisponible):
            await adapter.validar(cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso")

    async def test_should_raise_validacion_no_disponible_on_5xx_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "service unavailable"})

        adapter = TruoraAdapter(
            api_key="test-api-key",
            base_url="https://api.truora.test",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(ValidacionNoDisponible):
            await adapter.validar(cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso")
