"""Unit tests for `get_geocoding_provider`
(`inmuebles/infrastructure/proveedor.py`), vista-mapa-inmuebles-leaflet:
environment-based selection between `GeocodingFakeAdapter` (default) and
`NominatimAdapter` (`"nominatim"`, no credentials required unlike
`identidad`/`pagos`/`seguro_arrendamiento`'s providers).
"""

from __future__ import annotations

import pytest

from inmuebles.infrastructure.external.geocoding_fake_adapter import GeocodingFakeAdapter
from inmuebles.infrastructure.external.nominatim_adapter import NominatimAdapter
from inmuebles.infrastructure.proveedor import get_geocoding_provider
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetGeocodingProvider:
    def test_should_return_fake_adapter_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setattr(
            "inmuebles.infrastructure.proveedor.get_settings",
            lambda: Settings(inmuebles_geocoding_proveedor="fake"),
        )

        # Act
        proveedor = get_geocoding_provider()

        # Assert
        assert isinstance(proveedor, GeocodingFakeAdapter)

    def test_should_return_nominatim_adapter_when_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "inmuebles.infrastructure.proveedor.get_settings",
            lambda: Settings(inmuebles_geocoding_proveedor="nominatim"),
        )

        # Act
        proveedor = get_geocoding_provider()

        # Assert
        assert isinstance(proveedor, NominatimAdapter)
