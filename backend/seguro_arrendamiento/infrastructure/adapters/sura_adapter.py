"""`SuraAdapter` — production implementation of
`ProveedorSeguroArrendamientoPort`, backed by Sura's (ArriendeSeguro)
seguro de arrendamiento product (design.md decisión 1: chosen over Seguros
Bolívar for its digital-first, sin-codeudor product positioning).

The exact contract of Sura's API (endpoint path, payload shape, error
codes) is an explicit open question in design.md — Sura has no publicly
documented B2B API. Resolved here with the smallest reasonable shape
(`POST {base_url}/polizas`, multipart body, `Sura-API-Key` header, JSON
response with `estado`/`prima_mensual`/`vigencia_desde`/`vigencia_hasta`/
`referencia`) — adjust this adapter, not the domain port, once Sura's real
contract is confirmed against a sandbox account (same precedent as
`identidad.infrastructure.adapters.truora_adapter.TruoraAdapter`);
`ProveedorSeguroArrendamientoPort` and every caller are unaffected by that
change.
"""

from __future__ import annotations

from datetime import date

import httpx

from seguro_arrendamiento.domain.exceptions import ContratacionNoDisponible
from seguro_arrendamiento.domain.ports import ResultadoPoliza

_ESTADO_APROBADA = "aprobada"


class SuraAdapter:
    """Calls the real Sura API to contratar a seguro de arrendamiento."""

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

    async def contratar(self, *, cedula: str, documentos: list[bytes]) -> ResultadoPoliza:
        """Forward the contratación to Sura and discard the document bytes
        right after — this method never writes them anywhere else.

        Raises `ContratacionNoDisponible` on any timeout, network error, or
        non-2xx response, instead of letting the failure surface as an
        unhandled exception (which the API layer would otherwise turn into
        a 500).
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/polizas",
                headers={"Sura-API-Key": self._api_key},
                data={"cedula": cedula},
                files=[
                    (
                        "documentos",
                        (f"documento-{i}", documento, "application/octet-stream"),
                    )
                    for i, documento in enumerate(documentos)
                ],
            )
        except httpx.HTTPError as error:
            raise ContratacionNoDisponible(
                "El proveedor de seguro de arrendamiento no respondió"
            ) from error

        if response.status_code >= 400:
            raise ContratacionNoDisponible(
                f"El proveedor de seguro de arrendamiento respondió con error "
                f"({response.status_code})"
            )

        payload = response.json()
        aprobada = payload.get("estado") == _ESTADO_APROBADA
        return ResultadoPoliza(
            aprobada=aprobada,
            referencia_externa=payload.get("referencia", ""),
            prima_mensual=payload.get("prima_mensual") if aprobada else None,
            vigencia_desde=(
                date.fromisoformat(payload["vigencia_desde"])
                if aprobada and payload.get("vigencia_desde")
                else None
            ),
            vigencia_hasta=(
                date.fromisoformat(payload["vigencia_hasta"])
                if aprobada and payload.get("vigencia_hasta")
                else None
            ),
        )
