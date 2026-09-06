"""`FakeAdapter` — dev/test implementation of
`ProveedorFirmaElectronicaPort`.

Per design.md's flow diagram ("Fake: firma inmediato") and "Estrategia de
testing", this adapter always accepts the enviar-a-firma call and returns a
deterministic `referencia_externa`, so tests exercising the happy path
never need to mock a variable proveedor response — same pattern as
`seguro_arrendamiento.infrastructure.adapters.fake_adapter.FakeAdapter`.

Unlike a real provider (`ViafirmaAdapter`), the actual firma result
(firmado/rechazado/expirado) is never produced by this adapter's return
value — that always arrives later via the webhook
(`ResultadoFirmaWebhook`), per design.md's async flow. Tests that want to
simulate the full firmado/rechazado/expirado cycle in-process invoke
`firma_contrato.application.procesar_resultado_firma` directly with a
`ResultadoFirmaWebhook`, using this adapter's `referencia_externa` to
locate the contrato.
"""

from __future__ import annotations

import hashlib

from firma_contrato.domain.ports import ResultadoEnvioFirma


class FakeAdapter:
    """Always-accept implementation of `ProveedorFirmaElectronicaPort`,
    used as the default adapter in every environment until Viafirma
    credentials are configured (task 7.3)."""

    async def enviar_a_firma(self, *, documento: str) -> ResultadoEnvioFirma:
        """Return a `referencia_externa` deterministic on `documento` —
        useful for assertions in integration tests."""
        referencia_externa = f"FAKE-{hashlib.sha256(documento.encode('utf-8')).hexdigest()[:16]}"
        return ResultadoEnvioFirma(referencia_externa=referencia_externa)
