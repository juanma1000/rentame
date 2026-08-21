"""Outbound ports for the `inmuebles` domain.

These `Protocol`s are the interfaces the application layer (tasks 3.x-4.x of
`openspec/changes/hu-001/tasks.md`, e.g. `publicar_inmueble.py`) depends on
instead of depending on concrete infrastructure. Concrete adapters
(`InmuebleRepositoryPostgres`, `s3_storage_adapter.py`) are implemented in
`inmuebles/infrastructure/` in a later phase, per
`docs/architecture/architecture.md`'s hexagonal layout for this domain.

Methods are `async` because the project's persistence layer is built on
SQLAlchemy's async engine/session (see `shared/infrastructure/database.py`)
and the storage adapter performs network I/O against S3/MinIO.

`Protocol` (structural typing) is used rather than `ABC` since no shared
implementation is needed here — adapters only need to match the shape, not
inherit from a common base. No port existed yet elsewhere in the project to
follow as precedent, so this follows the interface shape implied by
`design.md`'s sequence diagram ("Publicación de inmueble") directly.
"""

from typing import Protocol
from uuid import UUID

from inmuebles.domain.inmueble import Inmueble


class InmuebleRepositoryPort(Protocol):
    """Persistence contract for the `Inmueble` aggregate."""

    async def guardar(self, inmueble: Inmueble) -> Inmueble:
        """Insert a new `Inmueble` (and its `fotos`) and return it with `id` set."""
        ...

    async def actualizar(self, inmueble: Inmueble) -> Inmueble:
        """Persist changes to an existing `Inmueble` (data edits and/or `estado`)."""
        ...

    async def obtener_por_id(self, inmueble_id: UUID) -> Inmueble | None:
        """Return the `Inmueble` matching `inmueble_id`, or `None` if it does not exist."""
        ...

    async def listar_por_propietario(self, propietario_id: UUID) -> list[Inmueble]:
        """Return every `Inmueble` owned by `propietario_id` (empty list if none)."""
        ...


class StoragePort(Protocol):
    """Object storage contract (S3/MinIO) used to persist inmueble photos.

    Per `design.md` decisión 1, the backend proxies the photo bytes
    (multipart upload) instead of issuing presigned URLs, so this port
    receives raw bytes rather than delegating the upload to the client.
    """

    async def subir_foto(self, inmueble_id: UUID, contenido: bytes, orden: int) -> str:
        """Upload one photo's bytes and return its `storage_key`."""
        ...

    def construir_url(self, storage_key: str) -> str:
        """Build the resolvable `url_storage` for a given `storage_key`."""
        ...
