"""Environment-based selection of the `ProveedorValidacionIdentidadPort`
adapter (task 6.3 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`).

`FakeAdapter` is the default in every environment until Truora credentials
are configured, per design.md's Migration Plan step 2 — a deliberate
production-safety default, not just a dev/test convenience.
"""

from __future__ import annotations

from identidad.domain.ports import ProveedorValidacionIdentidadPort
from identidad.infrastructure.adapters.fake_adapter import FakeAdapter
from shared.infrastructure.settings import get_settings


def get_proveedor_validacion_identidad() -> ProveedorValidacionIdentidadPort:
    """FastAPI dependency: build the `ProveedorValidacionIdentidadPort`
    adapter selected by `settings.identidad_proveedor`.

    `"truora"` requires `settings.truora_api_key` to be set (raises
    `ValueError` otherwise, surfacing a clear misconfiguration at startup of
    the first request rather than silently falling back). Any other value
    (including the default, `"fake"`) returns `FakeAdapter`.

    `TruoraAdapter` is imported lazily so this module (and every caller
    that only needs `FakeAdapter`, e.g. task 5's endpoint tests) never
    requires the HTTP client dependency `TruoraAdapter` needs (task 6).
    """
    settings = get_settings()
    if settings.identidad_proveedor == "truora":
        if not settings.truora_api_key:
            raise ValueError(
                "identidad_proveedor is 'truora' but truora_api_key is not configured"
            )
        from identidad.infrastructure.adapters.truora_adapter import TruoraAdapter

        return TruoraAdapter(api_key=settings.truora_api_key, base_url=settings.truora_base_url)
    return FakeAdapter()
