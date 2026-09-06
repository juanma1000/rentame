"""Application settings, loaded from environment variables via pydantic-settings.

All configuration values that vary between environments (local dev, CI,
staging, production) live here. Defaults are provided for local development
only — production deployments must override every secret via environment
variables (see `.env.example` at the repo root).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Rentame API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://rentame:rentame@localhost:5432/rentame"
    test_database_url: str = "postgresql+asyncpg://rentame:rentame@localhost:5432/rentame_test"

    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    storage_endpoint_url: str = "http://localhost:9000"
    # URL used to build `url_storage` values returned to clients. Distinct
    # from `storage_endpoint_url` because in Docker Compose the backend talks
    # to MinIO over the internal network (`http://minio:9000`), a hostname
    # browsers can never resolve — photo URLs must instead point at the
    # host-exposed port. Defaults to `storage_endpoint_url` for setups where
    # both are already reachable the same way (e.g. bare-metal dev).
    storage_public_url: str | None = None
    storage_access_key: str = "rentame"
    storage_secret_key: str = "rentame12345"
    storage_bucket_name: str = "inmuebles"
    storage_region: str = "us-east-1"

    max_fotos_inmueble: int = 10

    # `identidad` domain (`openspec/changes/validacion-identidad-inquilino`):
    # selects the `ProveedorValidacionIdentidadPort` adapter
    # (`identidad/infrastructure/proveedor.py`). `"fake"` (default) is safe
    # in every environment until Truora credentials are configured, per
    # design.md's Migration Plan step 2; only `"truora"` requires
    # `truora_api_key` to be set.
    identidad_proveedor: str = "fake"
    truora_api_key: str | None = None
    truora_base_url: str = "https://api.truora.com"

    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance.

    Cached with `lru_cache` so environment variables are read once per
    process. Tests that need different settings should call
    `get_settings.cache_clear()` first.
    """
    return Settings()
