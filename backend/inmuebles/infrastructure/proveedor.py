"""Environment-based selection of the `GeocodingPort` adapter
(vista-mapa-inmuebles-leaflet, design.md decisión 4).

`GeocodingFakeAdapter` (always returns `None`) is the default in every
environment; `"nominatim"` selects the real, key-less Nominatim API. Unlike
`identidad`/`pagos`/`seguro_arrendamiento`'s providers, no API key gate is
needed here — Nominatim is free and requires none.
"""

from __future__ import annotations

from inmuebles.domain.ports import GeocodingPort
from inmuebles.infrastructure.external.geocoding_fake_adapter import GeocodingFakeAdapter
from shared.infrastructure.settings import get_settings


def get_geocoding_provider() -> GeocodingPort:
    """FastAPI dependency: build the `GeocodingPort` adapter selected by
    `settings.inmuebles_geocoding_proveedor`.

    `"nominatim"` returns `NominatimAdapter` (imported lazily so callers
    that only need the fake adapter never require `httpx`, mirroring
    `identidad.infrastructure.proveedor`). Any other value (including the
    default, `"fake"`) returns `GeocodingFakeAdapter`.
    """
    settings = get_settings()
    if settings.inmuebles_geocoding_proveedor == "nominatim":
        from inmuebles.infrastructure.external.nominatim_adapter import NominatimAdapter

        return NominatimAdapter()
    return GeocodingFakeAdapter()
