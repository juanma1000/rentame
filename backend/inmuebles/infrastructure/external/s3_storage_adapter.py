"""`StoragePort` implementation backed by S3-compatible object storage (MinIO).

Per `design.md` decisión 1, the backend proxies photo bytes (multipart
upload) instead of issuing presigned URLs, so `subir_foto` receives raw
bytes and performs the `PUT object` itself via boto3, pointed at
`settings.storage_endpoint_url` (MinIO in local dev, per `docker-compose.yml`).

`boto3` is a synchronous client. Since `StoragePort.subir_foto` is `async`
(the port interface is uniform across adapters — see `ports.py`), the actual
network call is offloaded to a worker thread via `asyncio.to_thread` so it
never blocks the event loop, mirroring the "Patrones Async/Await" guidance in
`docs/backend-standards.md` (always `async`/`await`, never blocking calls
inline).
"""

import asyncio
import uuid
from uuid import UUID

import boto3
from botocore.client import Config

from shared.infrastructure.settings import Settings


class S3StorageAdapter:
    """S3/MinIO-backed adapter for `StoragePort`."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint_url,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            region_name=settings.storage_region,
            config=Config(signature_version="s3v4"),
        )

    async def subir_foto(self, inmueble_id: UUID, contenido: bytes, orden: int) -> str:
        """Upload one photo's bytes and return its `storage_key`."""
        storage_key = f"inmuebles/{inmueble_id}/{uuid.uuid4()}.jpg"

        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._settings.storage_bucket_name,
            Key=storage_key,
            Body=contenido,
            ContentType="image/jpeg",
        )

        return storage_key

    def construir_url(self, storage_key: str) -> str:
        """Build the resolvable `url_storage` for a given `storage_key`.

        Uses `storage_public_url` (browser-reachable) when configured,
        falling back to `storage_endpoint_url` — see `Settings.storage_public_url`.
        """
        endpoint = (self._settings.storage_public_url or self._settings.storage_endpoint_url).rstrip(
            "/"
        )
        return f"{endpoint}/{self._settings.storage_bucket_name}/{storage_key}"
