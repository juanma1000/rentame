"""Unit tests for `ViafirmaAdapter`
(`firma_contrato/infrastructure/adapters/viafirma_adapter.py`), task 7.1 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`.

The exact Viafirma contract is an explicit open question in design.md — no
publicly documented B2B API — so this adapter (and these tests) fix the
smallest reasonable shape, same precedent as
`tests/seguro_arrendamiento/infrastructure/test_sura_adapter.py` for
`SuraAdapter`. Uses a stubbed `httpx.AsyncClient` (via
`httpx.MockTransport`) rather than hitting the network.

TDD Red phase: `firma_contrato/infrastructure/adapters/viafirma_adapter.py`
does not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 7.2).
"""

from __future__ import annotations

import httpx
import pytest

from firma_contrato.domain.exceptions import EnvioFirmaNoDisponible
from firma_contrato.domain.ports import ResultadoEnvioFirma
from firma_contrato.infrastructure.adapters.viafirma_adapter import ViafirmaAdapter


def _client_with(handler) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, timeout=10.0)


class TestViafirmaAdapterEnviarAFirma:
    async def test_maps_successful_response_to_resultado_envio_firma(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path.endswith("/documentos")
            assert request.headers["Viafirma-Api-Key"] == "a-real-key"
            return httpx.Response(200, json={"id_documento": "viafirma-ref-123"})

        adapter = ViafirmaAdapter(
            api_key="a-real-key",
            base_url="https://api.viafirma.com.co",
            client=_client_with(handler),
        )

        # Act
        resultado = await adapter.enviar_a_firma(documento="contrato-texto-generado")

        # Assert
        assert isinstance(resultado, ResultadoEnvioFirma)
        assert resultado.referencia_externa == "viafirma-ref-123"

    async def test_raises_envio_firma_no_disponible_on_timeout(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        adapter = ViafirmaAdapter(
            api_key="a-real-key",
            base_url="https://api.viafirma.com.co",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(EnvioFirmaNoDisponible):
            await adapter.enviar_a_firma(documento="contrato-texto-generado")

    async def test_raises_envio_firma_no_disponible_on_error_response(self) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal"})

        adapter = ViafirmaAdapter(
            api_key="a-real-key",
            base_url="https://api.viafirma.com.co",
            client=_client_with(handler),
        )

        # Act / Assert
        with pytest.raises(EnvioFirmaNoDisponible):
            await adapter.enviar_a_firma(documento="contrato-texto-generado")
