"""Unit tests for `get_pasarela_pagos`
(`pagos/infrastructure/proveedor.py`), task 8.3 of
`openspec/changes/pago-mensual-renta/tasks.md`: environment-based
selection between `FakeAdapter` (default) and `WompiAdapter` (prod,
requires credentials).
"""

from __future__ import annotations

import pytest

from pagos.infrastructure.adapters.fake_adapter import FakeAdapter
from pagos.infrastructure.adapters.wompi_adapter import WompiAdapter
from pagos.infrastructure.proveedor import get_pasarela_pagos
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetPasarelaPagos:
    def test_should_return_fake_adapter_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setattr(
            "pagos.infrastructure.proveedor.get_settings",
            lambda: Settings(pagos_proveedor="fake"),
        )

        # Act
        pasarela = get_pasarela_pagos()

        # Assert
        assert isinstance(pasarela, FakeAdapter)

    def test_should_return_wompi_adapter_when_configured_with_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "pagos.infrastructure.proveedor.get_settings",
            lambda: Settings(pagos_proveedor="wompi", wompi_api_key="a-real-key"),
        )

        # Act
        pasarela = get_pasarela_pagos()

        # Assert
        assert isinstance(pasarela, WompiAdapter)

    def test_should_raise_when_wompi_selected_without_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "pagos.infrastructure.proveedor.get_settings",
            lambda: Settings(pagos_proveedor="wompi", wompi_api_key=None),
        )

        # Act / Assert
        with pytest.raises(ValueError):
            get_pasarela_pagos()
