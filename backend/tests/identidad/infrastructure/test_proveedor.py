"""Unit tests for `get_proveedor_validacion_identidad`
(`identidad/infrastructure/proveedor.py`), task 6.3 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`: environment-based
selection between `FakeAdapter` (default) and `TruoraAdapter` (prod, requires
credentials).
"""

from __future__ import annotations

import pytest

from identidad.infrastructure.adapters.fake_adapter import FakeAdapter
from identidad.infrastructure.adapters.truora_adapter import TruoraAdapter
from identidad.infrastructure.proveedor import get_proveedor_validacion_identidad
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetProveedorValidacionIdentidad:
    def test_should_return_fake_adapter_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        monkeypatch.setattr(
            "shared.infrastructure.settings.get_settings",
            lambda: Settings(identidad_proveedor="fake"),
        )
        monkeypatch.setattr(
            "identidad.infrastructure.proveedor.get_settings",
            lambda: Settings(identidad_proveedor="fake"),
        )

        # Act
        proveedor = get_proveedor_validacion_identidad()

        # Assert
        assert isinstance(proveedor, FakeAdapter)

    def test_should_return_truora_adapter_when_configured_with_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "identidad.infrastructure.proveedor.get_settings",
            lambda: Settings(identidad_proveedor="truora", truora_api_key="a-real-key"),
        )

        # Act
        proveedor = get_proveedor_validacion_identidad()

        # Assert
        assert isinstance(proveedor, TruoraAdapter)

    def test_should_raise_when_truora_selected_without_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "identidad.infrastructure.proveedor.get_settings",
            lambda: Settings(identidad_proveedor="truora", truora_api_key=None),
        )

        # Act / Assert
        with pytest.raises(ValueError):
            get_proveedor_validacion_identidad()
