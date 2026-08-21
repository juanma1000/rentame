"""Integration tests for `S3StorageAdapter` (`StoragePort` → boto3/MinIO).

Covers task 6.2 of `openspec/changes/hu-001/tasks.md`, per `design.md`'s
testing strategy ("`s3_storage_adapter`: test de integración contra MinIO
local (no mockeado) para validar el contrato real de `PUT object`"). Unlike
`backend/tests/inmuebles/application/conftest.py`'s `FakeStoragePort` (an
in-memory double used by the use case tests), this file exercises the real
adapter against the MinIO instance started by `docker-compose.yml`
(`rentame-minio`), using the same credentials/endpoint the app reads via
`shared.infrastructure.settings.get_settings()` (`STORAGE_*` env vars, see
`.env.example`).

TDD Red phase: `inmuebles/infrastructure/external/s3_storage_adapter.py`
(`S3StorageAdapter`, task 6.1) does not exist yet. Every test below is
therefore expected to fail at collection time with `ModuleNotFoundError`,
mirroring the precedent set by
`backend/tests/inmuebles/infrastructure/test_repository.py` for
`InmuebleRepositoryPostgres` before task 5.3 landed.

This file fixes, by construction, the contract `backend-expert` must satisfy
for `S3StorageAdapter` (no in-repo precedent existed yet for a storage
adapter):

- `S3StorageAdapter(settings)`: constructor takes the injected `Settings`
  instance (`shared.infrastructure.settings.Settings`), mirroring the single
  injected-dependency shape already used by `InmuebleRepositoryPostgres
  (session)`.
- `subir_foto(inmueble_id, contenido, orden)`: uploads `contenido` (raw
  bytes) to the configured bucket (`settings.storage_bucket_name`) via a real
  `PUT object` against `settings.storage_endpoint_url`, and returns a
  non-empty `storage_key` string that a `head_object`/`get_object` call made
  directly with boto3 (bypassing the adapter) can resolve.
- `construir_url(storage_key)`: returns a URL string that both references
  the given `storage_key` and points at the configured storage endpoint, so
  callers can build `FotoInmueble.url_storage` from it.

Every test uploads its own uniquely-named test object and deletes it in a
`finally` block, so no test-created object is left behind in the MinIO
bucket after the run (nothing here relies on transactional rollback, since
S3-compatible storage has no such concept).
"""

import uuid

import boto3
import pytest
import pytest_asyncio
from botocore.client import BaseClient, Config
from botocore.exceptions import ClientError

from inmuebles.infrastructure.external.s3_storage_adapter import S3StorageAdapter
from shared.infrastructure.settings import Settings, get_settings


@pytest.fixture(scope="module")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="module")
def raw_s3_client(settings: Settings) -> BaseClient:
    """A boto3 client built independently of the adapter under test.

    Used only to (a) make sure the test bucket exists before the adapter
    tries to upload into it, and (b) verify/clean up objects the adapter
    creates, without ever trusting `S3StorageAdapter`'s own reads to confirm
    its own writes.
    """
    client = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,
        config=Config(signature_version="s3v4"),
    )

    try:
        client.head_bucket(Bucket=settings.storage_bucket_name)
    except ClientError:
        client.create_bucket(Bucket=settings.storage_bucket_name)

    return client


@pytest_asyncio.fixture
async def storage_adapter(settings: Settings) -> S3StorageAdapter:
    return S3StorageAdapter(settings)


class TestS3StorageAdapterSubirFoto:
    async def test_should_upload_photo_and_return_a_storage_key_that_exists_in_minio(
        self,
        storage_adapter: S3StorageAdapter,
        raw_s3_client: BaseClient,
        settings: Settings,
    ) -> None:
        # Arrange
        inmueble_id = uuid.uuid4()
        contenido = f"fake-jpeg-bytes-{uuid.uuid4()}".encode()
        orden = 1
        storage_key = None

        try:
            # Act
            storage_key = await storage_adapter.subir_foto(inmueble_id, contenido, orden)

            # Assert: the adapter returned a usable key...
            assert isinstance(storage_key, str)
            assert storage_key != ""

            # ...and the object it claims to have uploaded is verifiably
            # present in the real MinIO bucket, verified independently via
            # boto3 rather than trusting the adapter's own return value.
            head = raw_s3_client.head_object(Bucket=settings.storage_bucket_name, Key=storage_key)
            assert head["ContentLength"] == len(contenido)

            get_result = raw_s3_client.get_object(
                Bucket=settings.storage_bucket_name, Key=storage_key
            )
            assert get_result["Body"].read() == contenido
        finally:
            # Cleanup: never leave test objects behind in MinIO.
            if storage_key is not None:
                raw_s3_client.delete_object(Bucket=settings.storage_bucket_name, Key=storage_key)


class TestS3StorageAdapterConstruirUrl:
    async def test_should_build_a_url_that_references_the_given_storage_key(
        self,
        storage_adapter: S3StorageAdapter,
    ) -> None:
        # Arrange
        storage_key = f"inmuebles/{uuid.uuid4()}/1.jpg"

        # Act
        url = storage_adapter.construir_url(storage_key)

        # Assert
        assert isinstance(url, str)
        assert storage_key in url
