"""Environment-based selection of the `PasarelaPagosPort` adapter (task
8.3 of `openspec/changes/pago-mensual-renta/tasks.md`).

`FakeAdapter` is the default in every environment until Wompi credentials
are configured, per design.md's Migration Plan step 3 — a deliberate
production-safety default, not just a dev/test convenience. Same mechanism
as `firma_contrato.infrastructure.proveedor.get_proveedor_firma_electronica`.
"""

from __future__ import annotations

from pagos.domain.ports import PasarelaPagosPort
from pagos.infrastructure.adapters.fake_adapter import FakeAdapter
from shared.infrastructure.settings import get_settings


def get_pasarela_pagos() -> PasarelaPagosPort:
    """FastAPI dependency: build the `PasarelaPagosPort` adapter selected
    by `settings.pagos_proveedor`.

    `"wompi"` requires `settings.wompi_api_key` to be set (raises
    `ValueError` otherwise, surfacing a clear misconfiguration at startup
    of the first request rather than silently falling back). Any other
    value (including the default, `"fake"`) returns `FakeAdapter`.

    `WompiAdapter` is imported lazily so this module (and every caller
    that only needs `FakeAdapter`) never requires the HTTP client
    dependency `WompiAdapter` needs.
    """
    settings = get_settings()
    if settings.pagos_proveedor == "wompi":
        if not settings.wompi_api_key:
            raise ValueError("pagos_proveedor is 'wompi' but wompi_api_key is not configured")
        from pagos.infrastructure.adapters.wompi_adapter import WompiAdapter

        return WompiAdapter(api_key=settings.wompi_api_key, base_url=settings.wompi_base_url)
    return FakeAdapter()
