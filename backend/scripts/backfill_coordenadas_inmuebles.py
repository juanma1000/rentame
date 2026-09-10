"""One-time backfill of `latitud`/`longitud` for inmuebles published before
`vista-mapa-inmuebles-leaflet` existed.

`publicar_inmueble`/`editar_inmueble` only geocode going forward (on
creation, or on edit when the location fields change) — see design.md's
"Migration Plan" step 3. Every inmueble that predates this change, and is
never edited afterward, would otherwise stay off the public map forever.
This script closes that gap: run it once, right after deploying this
change's backend code.

Unlike the synchronous call inside `publicar_inmueble`/`editar_inmueble`
(which accepts the risk of Nominatim's 1 request/second usage-policy limit
per design.md decisión 2, since it's a single request at a time), this
script processes many inmuebles in a tight loop and MUST throttle itself —
so it sleeps between calls, respecting that same limit explicitly.

Idempotent: only inmuebles with `latitud IS NULL` are considered, so
re-running after a partial run (or after new ungeocoded inmuebles appear)
only touches what's still missing.

Run with:
    docker compose exec backend python scripts/backfill_coordenadas_inmuebles.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from inmuebles.infrastructure.external.nominatim_adapter import NominatimAdapter
from inmuebles.infrastructure.persistence.models import InmuebleORM
from shared.infrastructure.database import AsyncSessionLocal

# `InmuebleORM.propietario_id`/`agente_id` are FKs to `usuario.id` — importing
# `UsuarioORM` registers that table on `Base.metadata` so SQLAlchemy can
# resolve the FK when flushing (same requirement `scripts/seed_data.py`
# documents for its own set of imports).
from usuarios.infrastructure.persistence.models import UsuarioORM  # noqa: F401

_NOMINATIM_RATE_LIMIT_SECONDS = 1.0


async def backfill() -> None:
    adapter = NominatimAdapter()

    async with AsyncSessionLocal() as session:
        modelos = (
            (
                await session.execute(
                    select(InmuebleORM).where(InmuebleORM.latitud.is_(None))
                )
            )
            .scalars()
            .all()
        )

        if not modelos:
            print("Ningún inmueble pendiente de geocodificar.")
            return

        print(f"Geocodificando {len(modelos)} inmueble(s)...")
        geocodificados = 0
        for modelo in modelos:
            coordenadas = await adapter.geocodificar(
                direccion=modelo.direccion, barrio=modelo.barrio, ciudad=modelo.ciudad
            )
            if coordenadas is not None:
                modelo.latitud = coordenadas.latitud
                modelo.longitud = coordenadas.longitud
                geocodificados += 1
                print(f"  - {modelo.id} ({modelo.direccion}): OK")
            else:
                print(f"  - {modelo.id} ({modelo.direccion}): sin resultado, se deja en null")

            await asyncio.sleep(_NOMINATIM_RATE_LIMIT_SECONDS)

        await session.commit()
        print(f"Listo: {geocodificados}/{len(modelos)} inmueble(s) geocodificados.")


if __name__ == "__main__":
    asyncio.run(backfill())
