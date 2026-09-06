"""Unit tests for `WompiAdapter`
(`pagos/infrastructure/adapters/wompi_adapter.py`), task 8.1 of
`openspec/changes/pago-mensual-renta/tasks.md`.

The exact Wompi "Pagos a Terceros API" contract is an explicit open
question in design.md — no confirmed commercial contract yet — so this
adapter (and these tests) fix the smallest reasonable shape, same
precedent as `tests/firma_contrato/infrastructure/test_viafirma_adapter.py`
for `ViafirmaAdapter`. Uses a stubbed `httpx.AsyncClient` (via
`httpx.MockTransport`) rather than hitting the network.

TDD Red phase: `pagos/infrastructure/adapters/wompi_adapter.py` does not
exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 8.2).
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from pagos.domain.exceptions import CobroPagoNoDisponible
from pagos.domain.ports import ResultadoCobro, SplitPago
from pagos.infrastructure.adapters.wompi_adapter import WompiAdapter


def _client_with(handler) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, timeout=10.0)


def _split() -> SplitPago:
    return SplitPago(
        monto_total=1_800_000.0,
        monto_prima_retenida=50_000.0,
        propietario_id=uuid.uuid4(),
    )


class TestWompiAdapterIniciarCobro:
    async def test_maps_successful_response_with_split_payload(self) -> None:
        # Arrange
        split = _split()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers["Authorization"] == "Bearer a-real-key"
            body = httpx.Request("POST", request.url, content=request.content).content
            import json

            payload = json.loads(body)
            assert payload["monto_total"] == split.monto_total
            assert payload["monto_prima_retenida"] == split.monto_prima_retenida
            assert payload["propietario_id"] == str(split.propietario_id)
            return httpx.Response(
                200, json={"id_transaccion": "wompi-ref-123", "estado": "pendiente"}
            )

        adapter = WompiAdapter(
            api_key="a-real-key",
            base_url="https://production.wompi.co/v1",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.iniciar_cobro(split)

        # Assert
        assert isinstance(resultado, ResultadoCobro)
        assert resultado.referencia_externa == "wompi-ref-123"
        assert resultado.estado == "pendiente"

    async def test_raises_cobro_pago_no_disponible_on_timeout(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        adapter = WompiAdapter(
            api_key="a-real-key",
            base_url="https://production.wompi.co/v1",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(CobroPagoNoDisponible):
            await adapter.iniciar_cobro(_split())

    async def test_raises_cobro_pago_no_disponible_on_error_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal"})

        adapter = WompiAdapter(
            api_key="a-real-key",
            base_url="https://production.wompi.co/v1",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(CobroPagoNoDisponible):
            await adapter.iniciar_cobro(_split())
