"""Unit tests for `get_proveedor_firma_electronica`
(`firma_contrato/infrastructure/proveedor.py`), task 7.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`:
environment-based selection between `FakeAdapter` (default) and
`ViafirmaAdapter` (prod, requires credentials).
"""

from __future__ import annotations

import pytest

from firma_contrato.infrastructure.adapters.fake_adapter import FakeAdapter
from firma_contrato.infrastructure.adapters.viafirma_adapter import ViafirmaAdapter
from firma_contrato.infrastructure.proveedor import get_proveedor_firma_electronica
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetProveedorFirmaElectronica:
    def test_should_return_fake_adapter_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setattr(
            "firma_contrato.infrastructure.proveedor.get_settings",
            lambda: Settings(firma_contrato_proveedor="fake"),
        )

        # Act
        proveedor = get_proveedor_firma_electronica()

        # Assert
        assert isinstance(proveedor, FakeAdapter)

    def test_should_return_viafirma_adapter_when_configured_with_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "firma_contrato.infrastructure.proveedor.get_settings",
            lambda: Settings(firma_contrato_proveedor="viafirma", viafirma_api_key="a-real-key"),
        )

        # Act
        proveedor = get_proveedor_firma_electronica()

        # Assert
        assert isinstance(proveedor, ViafirmaAdapter)

    def test_should_raise_when_viafirma_selected_without_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "firma_contrato.infrastructure.proveedor.get_settings",
            lambda: Settings(firma_contrato_proveedor="viafirma", viafirma_api_key=None),
        )

        # Act / Assert
        with pytest.raises(ValueError):
            get_proveedor_firma_electronica()
