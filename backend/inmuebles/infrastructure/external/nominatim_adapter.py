"""`NominatimAdapter` — production implementation of `GeocodingPort`, backed
by Nominatim's public search API (OpenStreetMap).

Chosen over a commercial geocoder (Google Geocoding, Mapbox, LocationIQ) for
this iteration because it requires no API key/cost, and because the map view
it feeds already uses OpenStreetMap tiles (vista-mapa-inmuebles-leaflet,
design.md decisión 2) — revisit if publication volume outgrows Nominatim's
1 request/second usage-policy limit (no client-side handling of that limit
exists here; see design.md decisión 2 and the standalone backfill script,
which does throttle its own calls).

Per design.md decisión 4, this adapter's `geocodificar` NEVER raises: a
timeout, connection error, non-2xx response, empty result set, or a result
missing `lat`/`lon` all resolve to `None` instead of an exception — the
domain never needs a try/except around this call, unlike `TruoraAdapter`
(identidad) which does raise on failure.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import httpx

from inmuebles.domain.ports import Coordenadas

_NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "Rentame/1.0 (contacto@rentame.test)"


class NominatimAdapter:
    """Calls the real Nominatim API to geocode a free-form address."""

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def geocodificar(
        self, *, direccion: str, barrio: str, ciudad: str
    ) -> Coordenadas | None:
        query = ", ".join(parte for parte in (direccion, barrio, ciudad) if parte)
        try:
            response = await self._client.get(
                _NOMINATIM_SEARCH_URL,
                params={"q": query, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": _USER_AGENT},
            )
        except httpx.HTTPError:
            return None

        if response.status_code >= 400:
            return None

        try:
            resultados = response.json()
            primero = resultados[0]
            return Coordenadas(
                latitud=Decimal(primero["lat"]),
                longitud=Decimal(primero["lon"]),
            )
        except (IndexError, KeyError, TypeError, ValueError, InvalidOperation):
            return None
