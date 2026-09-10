"""Unit tests for `GeocodingFakeAdapter`
(`inmuebles/infrastructure/external/geocoding_fake_adapter.py`).

Mirrors the style of `identidad`/`pagos`/`seguro_arrendamiento`'s
`fake_adapter.py` tests: a deterministic double used as the default
`GeocodingPort` in every environment until Nominatim is wired in
(vista-mapa-inmuebles-leaflet, design.md decisión 4). Never raises — the
port's contract forbids it.
"""

from __future__ import annotations

from decimal import Decimal

from inmuebles.domain.ports import Coordenadas
from inmuebles.infrastructure.external.geocoding_fake_adapter import GeocodingFakeAdapter


class TestGeocodingFakeAdapterConfiguredCoordenadas:
    async def test_should_return_configured_coordenadas(self) -> None:
        # Arrange
        coordenadas = Coordenadas(latitud=Decimal("6.244203"), longitud=Decimal("-75.581212"))
        adapter = GeocodingFakeAdapter(coordenadas=coordenadas)

        # Act
        resultado = await adapter.geocodificar(
            direccion="Calle 10 # 20-30", barrio="El Poblado", ciudad="Medellin"
        )

        # Assert
        assert resultado == coordenadas


class TestGeocodingFakeAdapterDefault:
    async def test_should_return_none_by_default(self) -> None:
        # Arrange
        adapter = GeocodingFakeAdapter()

        # Act
        resultado = await adapter.geocodificar(
            direccion="Calle 10 # 20-30", barrio="El Poblado", ciudad="Medellin"
        )

        # Assert
        assert resultado is None
