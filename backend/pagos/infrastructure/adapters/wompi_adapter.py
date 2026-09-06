"""`WompiAdapter` — production implementation of `PasarelaPagosPort`,
backed by Wompi's "Pagos a Terceros API" (design.md decisión 1: chosen
over PayU/ePayco for having split-de-pagos-a-terceros support documented
publicly, matching this domain's need to retain the prima and route the
neto to the propietario within the same transaction).

The exact contract of Wompi's Pagos a Terceros API (endpoint path,
payload shape, error codes, commission/retention detail) is an explicit
open question in design.md — no confirmed commercial contract yet.
Resolved here with the smallest reasonable shape (`POST
{base_url}/pagos-terceros`, JSON body with the split, `Authorization:
Bearer <api_key>` header, JSON response with `id_transaccion`/`estado`) —
adjust this adapter, not the domain port, once Wompi's real contract is
confirmed (same precedent as
`firma_contrato.infrastructure.adapters.viafirma_adapter.ViafirmaAdapter`);
`PasarelaPagosPort` and every caller are unaffected by that change.

`estado` in the response is passed through unchanged (Wompi's own
vocabulary) — `pagos.application.iniciar_pago` is the only place that
interprets it (`"completado"` vs. anything else, treated as pending/async).
"""

from __future__ import annotations

import httpx

from pagos.domain.exceptions import CobroPagoNoDisponible
from pagos.domain.ports import ResultadoCobro, SplitPago


class WompiAdapter:
    """Calls the real Wompi API to iniciar un cobro con split a
    terceros."""

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

    async def iniciar_cobro(self, split: SplitPago) -> ResultadoCobro:
        """Forward `split` to Wompi to iniciar el cobro con split a
        terceros.

        Raises `CobroPagoNoDisponible` on any timeout, network error, or
        non-2xx response, instead of letting the failure surface as an
        unhandled exception (which the API layer would otherwise turn
        into a 500).
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/pagos-terceros",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "monto_total": split.monto_total,
                    "monto_prima_retenida": split.monto_prima_retenida,
                    "propietario_id": str(split.propietario_id),
                },
            )
        except httpx.HTTPError as error:
            raise CobroPagoNoDisponible("La pasarela de pagos no respondió") from error

        if response.status_code >= 400:
            raise CobroPagoNoDisponible(
                f"La pasarela de pagos respondió con error ({response.status_code})"
            )

        payload = response.json()
        return ResultadoCobro(
            referencia_externa=payload.get("id_transaccion", ""),
            estado=payload.get("estado", "pendiente"),
        )
