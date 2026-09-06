"""Environment-based selection of the `ProveedorFirmaElectronicaPort`
adapter (task 7.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

`FakeAdapter` is the default in every environment until Viafirma
credentials are configured, per design.md's Migration Plan step 2 — a
deliberate production-safety default, not just a dev/test convenience.
Same mechanism as
`seguro_arrendamiento.infrastructure.proveedor.get_proveedor_seguro_arrendamiento`.
"""

from __future__ import annotations

from firma_contrato.domain.ports import ProveedorFirmaElectronicaPort
from firma_contrato.infrastructure.adapters.fake_adapter import FakeAdapter
from shared.infrastructure.settings import get_settings


def get_proveedor_firma_electronica() -> ProveedorFirmaElectronicaPort:
    """FastAPI dependency: build the `ProveedorFirmaElectronicaPort`
    adapter selected by `settings.firma_contrato_proveedor`.

    `"viafirma"` requires `settings.viafirma_api_key` to be set (raises
    `ValueError` otherwise, surfacing a clear misconfiguration at startup
    of the first request rather than silently falling back). Any other
    value (including the default, `"fake"`) returns `FakeAdapter`.

    `ViafirmaAdapter` is imported lazily so this module (and every caller
    that only needs `FakeAdapter`, e.g. task 6's endpoint tests) never
    requires the HTTP client dependency `ViafirmaAdapter` needs (task 7).
    """
    settings = get_settings()
    if settings.firma_contrato_proveedor == "viafirma":
        if not settings.viafirma_api_key:
            raise ValueError(
                "firma_contrato_proveedor is 'viafirma' but viafirma_api_key is not configured"
            )
        from firma_contrato.infrastructure.adapters.viafirma_adapter import ViafirmaAdapter

        return ViafirmaAdapter(
            api_key=settings.viafirma_api_key, base_url=settings.viafirma_base_url
        )
    return FakeAdapter()
