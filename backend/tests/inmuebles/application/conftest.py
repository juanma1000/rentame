"""In-memory fakes for the `inmuebles` outbound ports (`InmuebleRepositoryPort`,
`StoragePort`, `inmuebles/domain/ports.py`), shared by every application-layer
(use case) test in this package.

These fakes are test doubles only — no production code lives here. They exist
purely so the use case tests (tasks 3.1-3.9 of `openspec/changes/hu-001/
tasks.md`) can exercise `inmuebles/application/*` in isolation, without a real
database or S3/MinIO connection, per `design.md`'s testing strategy
("Casos de uso ... tests unitarios con repositorio e storage adapter
fake/in-memory").

Both fakes satisfy the `Protocol`s defined in `inmuebles/domain/ports.py`
structurally (no inheritance needed, per that module's docstring).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from inmuebles.domain.ports import Coordenadas


@dataclass
class FakeInmuebleRepository:
    """In-memory stand-in for `InmuebleRepositoryPort`.

    Accepts an initial collection of already-`crear`d `Inmueble`s to seed the
    fake (assigning an `id` to each if it doesn't have one yet, mimicking
    what a real repository's `guardar` would have done previously). Records
    every `guardar`/`actualizar` call so tests can assert on side effects
    (e.g. "must NOT call `actualizar` when authorization fails").
    """

    _inmuebles: dict[UUID, Inmueble] = field(default_factory=dict)
    guardar_calls: list[Inmueble] = field(default_factory=list)
    actualizar_calls: list[Inmueble] = field(default_factory=list)

    def seed(self, inmueble: Inmueble) -> Inmueble:
        """Register a pre-existing `Inmueble` in the fake, assigning an `id`
        if missing, and return it (with `id` set)."""
        if inmueble.id is None:
            inmueble.id = uuid4()
        self._inmuebles[inmueble.id] = inmueble
        return inmueble

    async def guardar(self, inmueble: Inmueble) -> Inmueble:
        self.guardar_calls.append(inmueble)
        inmueble.id = uuid4()
        self._inmuebles[inmueble.id] = inmueble
        return inmueble

    async def actualizar(self, inmueble: Inmueble) -> Inmueble:
        self.actualizar_calls.append(inmueble)
        if inmueble.id is None:
            raise AssertionError("actualizar() called with an Inmueble that has no id")
        self._inmuebles[inmueble.id] = inmueble
        return inmueble

    async def obtener_por_id(self, inmueble_id: UUID) -> Inmueble | None:
        return self._inmuebles.get(inmueble_id)

    async def listar_por_propietario(self, propietario_id: UUID) -> list[Inmueble]:
        return [
            inmueble
            for inmueble in self._inmuebles.values()
            if inmueble.propietario_id == propietario_id
        ]

    async def listar_por_propietarios(self, propietario_ids: list[UUID]) -> list[Inmueble]:
        """In-memory stand-in for the `hu-002` port method (design.md
        decisión 6) backing `listar_inmuebles_gestionados`. Returns every
        `Inmueble` whose `propietario_id` is in `propietario_ids` (empty list
        when `propietario_ids` is empty, same as a real `WHERE ... IN ()`)."""
        propietario_id_set = set(propietario_ids)
        return [
            inmueble
            for inmueble in self._inmuebles.values()
            if inmueble.propietario_id in propietario_id_set
        ]

    async def listar_disponibles(self) -> list[Inmueble]:
        """In-memory stand-in for the `hu-003` port method (design.md
        decisión 2) backing `listar_inmuebles_publicos`. Returns every
        `Inmueble` whose `estado` is `EstadoInmueble.DISPONIBLE` (empty list
        when none match), mirroring the `WHERE estado = 'disponible'` filter
        the real `InmuebleRepositoryPostgres.listar_disponibles()` will run."""
        return [
            inmueble
            for inmueble in self._inmuebles.values()
            if inmueble.estado == EstadoInmueble.DISPONIBLE
        ]


@dataclass
class FakeStoragePort:
    """In-memory stand-in for `StoragePort`.

    Stores every uploaded photo's bytes in memory (keyed by the generated
    `storage_key`) instead of talking to S3/MinIO, and builds a deterministic,
    inspectable fake URL.
    """

    uploaded: dict[str, bytes] = field(default_factory=dict)
    subir_foto_calls: list[tuple[UUID, bytes, int]] = field(default_factory=list)

    async def subir_foto(self, inmueble_id: UUID, contenido: bytes, orden: int) -> str:
        self.subir_foto_calls.append((inmueble_id, contenido, orden))
        storage_key = f"inmuebles/{inmueble_id}/{orden}.jpg"
        self.uploaded[storage_key] = contenido
        return storage_key

    def construir_url(self, storage_key: str) -> str:
        return f"https://fake-storage.test/{storage_key}"


@dataclass
class FakeGeocodingPort:
    """In-memory stand-in for `GeocodingPort` (vista-mapa-inmuebles-leaflet).

    Returns `coordenadas` (`None` by default) regardless of the address
    given, and records every call so tests can assert whether
    `publicar_inmueble`/`editar_inmueble` invoked it or not (design.md
    decisión 3: `editar_inmueble` must skip this call when the location
    fields didn't change)."""

    coordenadas: Coordenadas | None = None
    geocodificar_calls: list[tuple[str, str, str]] = field(default_factory=list)

    async def geocodificar(
        self, *, direccion: str, barrio: str, ciudad: str
    ) -> Coordenadas | None:
        self.geocodificar_calls.append((direccion, barrio, ciudad))
        return self.coordenadas


@pytest.fixture
def fake_repository() -> FakeInmuebleRepository:
    return FakeInmuebleRepository()


@pytest.fixture
def fake_storage() -> FakeStoragePort:
    return FakeStoragePort()


@pytest.fixture
def fake_geocoding() -> FakeGeocodingPort:
    return FakeGeocodingPort()
