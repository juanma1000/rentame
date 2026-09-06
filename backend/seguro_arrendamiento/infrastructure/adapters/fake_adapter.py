"""`FakeAdapter` — dev/test implementation of
`ProveedorSeguroArrendamientoPort`.

Per design.md's "Estrategia de testing": always approves, so happy-path
tests never need to mock a variable proveedor response. Tests covering the
rejection path inject their own stub of `ProveedorSeguroArrendamientoPort`
instead of touching this adapter (task 3.2 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`), same pattern
as `identidad.infrastructure.adapters.fake_adapter.FakeAdapter`.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

from seguro_arrendamiento.domain.ports import ResultadoPoliza

_PRIMA_MENSUAL = 45000.0
_VIGENCIA_DIAS = 365


class FakeAdapter:
    """Always-approve implementation of `ProveedorSeguroArrendamientoPort`,
    used as the default adapter in every environment until Sura credentials
    are configured (task 6.3)."""

    async def contratar(self, *, cedula: str, documentos: list[bytes]) -> ResultadoPoliza:
        """Discard the document bytes immediately (never persisted, per
        spec.md) and return an approved result with a `prima_mensual` and
        `referencia_externa` deterministic on `cedula` — useful for
        assertions in integration tests."""
        referencia_externa = f"FAKE-{hashlib.sha256(cedula.encode('utf-8')).hexdigest()[:16]}"
        vigencia_desde = date.today()
        vigencia_hasta = vigencia_desde + timedelta(days=_VIGENCIA_DIAS)
        return ResultadoPoliza(
            aprobada=True,
            referencia_externa=referencia_externa,
            prima_mensual=_PRIMA_MENSUAL,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
        )
