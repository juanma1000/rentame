"""`GeocodingFakeAdapter` — dev/test implementation of `GeocodingPort`
(vista-mapa-inmuebles-leaflet, design.md decisión 4).

Default adapter in every environment until `inmuebles_geocoding_proveedor`
selects `"nominatim"`, mirroring `identidad`/`pagos`/`seguro_arrendamiento`'s
`FakeAdapter` convention.
"""

from __future__ import annotations

from inmuebles.domain.ports import Coordenadas


class GeocodingFakeAdapter:
    """Returns whatever `coordenadas` it was built with (`None` by
    default), never raising — same contract as the real `NominatimAdapter`."""

    def __init__(self, coordenadas: Coordenadas | None = None) -> None:
        self._coordenadas = coordenadas

    async def geocodificar(
        self, *, direccion: str, barrio: str, ciudad: str
    ) -> Coordenadas | None:
        return self._coordenadas
