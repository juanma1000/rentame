"""Unit tests for `get_proveedor_seguro_arrendamiento`
(`seguro_arrendamiento/infrastructure/proveedor.py`), task 6.3 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`:
environment-based selection between `FakeAdapter` (default) and
`SuraAdapter` (prod, requires credentials).
"""

from __future__ import annotations

import pytest

from seguro_arrendamiento.infrastructure.adapters.fake_adapter import FakeAdapter
from seguro_arrendamiento.infrastructure.adapters.sura_adapter import SuraAdapter
from seguro_arrendamiento.infrastructure.proveedor import get_proveedor_seguro_arrendamiento
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetProveedorSeguroArrendamiento:
    def test_should_return_fake_adapter_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setattr(
            "seguro_arrendamiento.infrastructure.proveedor.get_settings",
            lambda: Settings(seguro_arrendamiento_proveedor="fake"),
        )

        # Act
        proveedor = get_proveedor_seguro_arrendamiento()

        # Assert
        assert isinstance(proveedor, FakeAdapter)

    def test_should_return_sura_adapter_when_configured_with_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "seguro_arrendamiento.infrastructure.proveedor.get_settings",
            lambda: Settings(seguro_arrendamiento_proveedor="sura", sura_api_key="a-real-key"),
        )

        # Act
        proveedor = get_proveedor_seguro_arrendamiento()

        # Assert
        assert isinstance(proveedor, SuraAdapter)

    def test_should_raise_when_sura_selected_without_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "seguro_arrendamiento.infrastructure.proveedor.get_settings",
            lambda: Settings(seguro_arrendamiento_proveedor="sura", sura_api_key=None),
        )

        # Act / Assert
        with pytest.raises(ValueError):
            get_proveedor_seguro_arrendamiento()
