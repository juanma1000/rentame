"""`ViafirmaAdapter` — production implementation of
`ProveedorFirmaElectronicaPort`, backed by Viafirma's firma electrónica
product (design.md decisión 1: chosen over Docusign/Zoho Sign for its
Colombia-specific presence and Ley 527/1999 documentation).

The exact contract of Viafirma's API (endpoint path, payload shape, error
codes) is an explicit open question in design.md — no publicly documented
B2B API. Resolved here with the smallest reasonable shape (`POST
{base_url}/documentos`, JSON body with the document text, `Viafirma-Api-Key`
header, JSON response with `id_documento`) — adjust this adapter, not the
domain port, once Viafirma's real contract is confirmed against a sandbox
account (same precedent as
`seguro_arrendamiento.infrastructure.adapters.sura_adapter.SuraAdapter`);
`ProveedorFirmaElectronicaPort` and every caller are unaffected by that
change.
"""

from __future__ import annotations

import httpx

from firma_contrato.domain.exceptions import EnvioFirmaNoDisponible
from firma_contrato.domain.ports import ResultadoEnvioFirma


class ViafirmaAdapter:
    """Calls the real Viafirma API to send a documento a firma."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def enviar_a_firma(self, *, documento: str) -> ResultadoEnvioFirma:
        """Forward `documento` to Viafirma for gestionar el proceso de
        firma.

        Raises `EnvioFirmaNoDisponible` on any timeout, network error, or
        non-2xx response, instead of letting the failure surface as an
        unhandled exception (which the API layer would otherwise turn into
        a 500).
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/documentos",
                headers={"Viafirma-Api-Key": self._api_key},
                json={"documento": documento},
            )
        except httpx.HTTPError as error:
            raise EnvioFirmaNoDisponible(
                "El proveedor de firma electrónica no respondió"
            ) from error

        if response.status_code >= 400:
            raise EnvioFirmaNoDisponible(
                f"El proveedor de firma electrónica respondió con error "
                f"({response.status_code})"
            )

        payload = response.json()
        return ResultadoEnvioFirma(referencia_externa=payload.get("id_documento", ""))
