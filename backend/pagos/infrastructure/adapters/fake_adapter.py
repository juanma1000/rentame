"""`FakeAdapter` — dev/test implementation of `PasarelaPagosPort`.

Per design.md's flow diagram ("Fake: completa inmediato") and "Estrategia
de testing", this adapter always accepts the `iniciar_cobro` call and
returns a `completado` resultado with a deterministic `referencia_externa`
— same pattern as
`firma_contrato.infrastructure.adapters.fake_adapter.FakeAdapter`.

Unlike a real provider (`WompiAdapter`), this adapter never leaves a
`Pago` waiting on the webhook: tests exercising the happy path never need
to simulate `POST /pagos/webhook` separately, since `iniciar_pago` already
observes `estado == "completado"` synchronously.
"""

from __future__ import annotations

import hashlib

from pagos.domain.ports import ResultadoCobro, SplitPago


class FakeAdapter:
    """Always-accept implementation of `PasarelaPagosPort`, used as the
    default adapter in every environment until Wompi credentials are
    configured (task 8.3)."""

    async def iniciar_cobro(self, split: SplitPago) -> ResultadoCobro:
        """Return a `referencia_externa` deterministic on `split` —
        useful for assertions in integration tests."""
        base = f"{split.monto_total}-{split.monto_prima_retenida}-{split.propietario_id}"
        referencia_externa = f"FAKE-{hashlib.sha256(base.encode('utf-8')).hexdigest()[:16]}"
        return ResultadoCobro(referencia_externa=referencia_externa, estado="completado")
