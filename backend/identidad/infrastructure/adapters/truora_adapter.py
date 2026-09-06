"""`TruoraAdapter` — production implementation of
`ProveedorValidacionIdentidadPort`, backed by Truora's cédula-verification
API (design.md decisión 1: chosen over Jumio/Onfido for Colombian coverage
and cost).

The exact contract of Truora's API (endpoint path, payload shape, error
codes) is an open question in design.md, resolved here with the smallest
reasonable shape (`POST {base_url}/checks`, multipart body, `Truora-API-Key`
header, JSON response with `status`/`check_id`) — adjust this adapter, not
the domain port, once Truora's real contract is confirmed against a
sandbox account; `ProveedorValidacionIdentidadPort` and every caller are
unaffected by that change.
"""

from __future__ import annotations

import httpx

from identidad.domain.exceptions import ValidacionNoDisponible
from identidad.domain.ports import ResultadoValidacion

_ESTADO_APROBADO = "success"


class TruoraAdapter:
    """Calls the real Truora API to validate a cédula colombiana."""

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

    async def validar(
        self, *, cedula: str, imagen_frente: bytes, imagen_dorso: bytes
    ) -> ResultadoValidacion:
        """Forward the check to Truora and discard the image bytes right
        after — this method never writes them anywhere else.

        Raises `ValidacionNoDisponible` on any timeout, network error, or
        non-2xx response, instead of letting the failure surface as an
        unhandled exception (which the API layer would otherwise turn into
        a 500).
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/checks",
                headers={"Truora-API-Key": self._api_key},
                data={"national_id": cedula, "country": "CO"},
                files={
                    "document_front": ("frente.jpg", imagen_frente, "application/octet-stream"),
                    "document_back": ("dorso.jpg", imagen_dorso, "application/octet-stream"),
                },
            )
        except httpx.HTTPError as error:
            raise ValidacionNoDisponible(
                "El proveedor de validación de identidad no respondió"
            ) from error

        if response.status_code >= 400:
            raise ValidacionNoDisponible(
                f"El proveedor de validación de identidad respondió con error "
                f"({response.status_code})"
            )

        payload = response.json()
        return ResultadoValidacion(
            aprobado=payload.get("status") == _ESTADO_APROBADO,
            referencia_externa=payload.get("check_id", ""),
        )
