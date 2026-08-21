"""Value object representing a single photo attached to an `Inmueble`.

Fields mirror the `FOTO_INMUEBLE` entity from
`docs/architecture/architecture.md` and the "Carga de fotos en la
publicación" requirement in
`openspec/changes/hu-001/specs/inmuebles/spec.md`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FotoInmueble:
    """Immutable value object for a photo already stored in object storage.

    `url_storage` is the resolvable URL used to display the photo and
    `storage_key` is the key that addresses the object within the configured
    bucket (S3/MinIO, see `StoragePort`). `orden` fixes the 1-based display
    order and `es_principal` marks the cover photo shown in listings.
    """

    url_storage: str
    storage_key: str
    orden: int
    es_principal: bool
