"""Unit tests for `NominatimAdapter`
(`inmuebles/infrastructure/external/nominatim_adapter.py`).

Mirrors `tests/identidad/infrastructure/test_truora_adapter.py`'s style: the
real Nominatim API is never called in CI — every test injects an
`httpx.AsyncClient` built with `httpx.MockTransport`. Unlike `TruoraAdapter`,
this adapter never raises (vista-mapa-inmuebles-leaflet, design.md decisión
4): a timeout, error response, or empty result all resolve to `None`, since
geocoding failure must never block publishing/editing an inmueble.
"""

from __future__ import annotations

from decimal import Decimal

import httpx

from inmuebles.domain.ports import Coordenadas
from inmuebles.infrastructure.external.nominatim_adapter import NominatimAdapter


def _client_with(handler) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


class TestNominatimAdapterExito:
    async def test_should_return_coordenadas_when_nominatim_finds_a_result(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            assert "User-Agent" in request.headers
            assert request.url.params["format"] == "jsonv2"
            return httpx.Response(
                200,
                json=[{"lat": "6.2442030", "lon": "-75.5812119", "display_name": "El Poblado"}],
            )

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(
            direccion="Calle 10 # 20-30", barrio="El Poblado", ciudad="Medellin"
        )

        # Assert
        assert resultado == Coordenadas(
            latitud=Decimal("6.2442030"), longitud=Decimal("-75.5812119")
        )


class TestNominatimAdapterSinResultado:
    async def test_should_return_none_when_nominatim_finds_no_result(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(
            direccion="Direccion inexistente", barrio="", ciudad="Nowhere"
        )

        # Assert
        assert resultado is None


class TestNominatimAdapterFallos:
    async def test_should_return_none_on_timeout(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(direccion="X", barrio="Y", ciudad="Z")

        # Assert
        assert resultado is None

    async def test_should_return_none_on_connect_error(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(direccion="X", barrio="Y", ciudad="Z")

        # Assert
        assert resultado is None

    async def test_should_return_none_on_5xx_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "service unavailable"})

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(direccion="X", barrio="Y", ciudad="Z")

        # Assert
        assert resultado is None

    async def test_should_return_none_on_4xx_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad request"})

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(direccion="X", barrio="Y", ciudad="Z")

        # Assert
        assert resultado is None

    async def test_should_return_none_on_malformed_json_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"display_name": "sin lat/lon"}])

        adapter = NominatimAdapter(client=_client_with(handler))

        # Act
        resultado = await adapter.geocodificar(direccion="X", barrio="Y", ciudad="Z")

        # Assert
        assert resultado is None
