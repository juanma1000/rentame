"""Environment-based selection of the `ProveedorSeguroArrendamientoPort`
adapter (task 6.3 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`).

`FakeAdapter` is the default in every environment until Sura credentials
are configured, per design.md's Migration Plan step 2 — a deliberate
production-safety default, not just a dev/test convenience. Same mechanism
as `identidad.infrastructure.proveedor.get_proveedor_validacion_identidad`.
"""

from __future__ import annotations

from seguro_arrendamiento.domain.ports import ProveedorSeguroArrendamientoPort
from seguro_arrendamiento.infrastructure.adapters.fake_adapter import FakeAdapter
from shared.infrastructure.settings import get_settings


def get_proveedor_seguro_arrendamiento() -> ProveedorSeguroArrendamientoPort:
    """FastAPI dependency: build the `ProveedorSeguroArrendamientoPort`
    adapter selected by `settings.seguro_arrendamiento_proveedor`.

    `"sura"` requires `settings.sura_api_key` to be set (raises
    `ValueError` otherwise, surfacing a clear misconfiguration at startup of
    the first request rather than silently falling back). Any other value
    (including the default, `"fake"`) returns `FakeAdapter`.

    `SuraAdapter` is imported lazily so this module (and every caller that
    only needs `FakeAdapter`, e.g. task 5's endpoint tests) never requires
    the HTTP client dependency `SuraAdapter` needs (task 6).
    """
    settings = get_settings()
    if settings.seguro_arrendamiento_proveedor == "sura":
        if not settings.sura_api_key:
            raise ValueError(
                "seguro_arrendamiento_proveedor is 'sura' but sura_api_key is not configured"
            )
        from seguro_arrendamiento.infrastructure.adapters.sura_adapter import SuraAdapter

        return SuraAdapter(api_key=settings.sura_api_key, base_url=settings.sura_base_url)
    return FakeAdapter()
