"""Unit tests for the `publicar_inmueble` use case
(`inmuebles/application/publicar_inmueble.py`).

Covers tasks 3.1-3.2 of `openspec/changes/hu-001/tasks.md` and the
"Creación de publicación de inmueble" / "Carga de fotos en la publicación" /
"Estado inicial de la publicación" requirements of
`openspec/changes/hu-001/specs/inmuebles/spec.md`.

TDD Red phase: `inmuebles/application/publicar_inmueble.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (tasks 4.1, 4.5). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `FotoParaPublicar`: a plain dataclass carrying one photo's raw
  `contenido: bytes` and its `es_principal: bool` flag, as received from the
  multipart request before any upload happens.
- `PublicarInmuebleCommand`: a plain dataclass mirroring every field
  `Inmueble.crear` needs (`propietario_id`, `direccion`, `barrio`, `ciudad`,
  `tipo`, `area_m2`, `habitaciones`, `banos`, `valor_mensual`,
  `descripcion`) plus `fotos: list[FotoParaPublicar]`.
- `publicar_inmueble(command, *, repository, storage) -> Inmueble`: an async
  function (not a class) that:
  1. Uploads each `command.fotos[i]` via `storage.subir_foto(...)`
     (1-based `orden`) and builds the corresponding `FotoInmueble` via
     `storage.construir_url(...)`.
  2. Delegates every field/photo-count validation to `Inmueble.crear` —
     it must NOT re-implement any of those rules itself, only propagate the
     `DomainValidationError` `Inmueble.crear` raises.
  3. Persists the resulting `Inmueble` via `repository.guardar(...)` and
     returns the persisted instance (with `id` set, `estado == DISPONIBLE`).
  4. On validation failure, `repository.guardar` must NOT be called.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from inmuebles.application.publicar_inmueble import (
    FotoParaPublicar,
    PublicarInmuebleCommand,
    publicar_inmueble,
)
from inmuebles.domain.inmueble import EstadoInmueble
from shared.domain.exceptions import DomainValidationError
from tests.inmuebles.application.conftest import FakeInmuebleRepository, FakeStoragePort


def _build_foto_para_publicar(*, es_principal: bool = False) -> FotoParaPublicar:
    return FotoParaPublicar(contenido=b"fake-jpeg-bytes", es_principal=es_principal)


def _valid_command(**overrides: object) -> PublicarInmuebleCommand:
    kwargs: dict[str, object] = {
        "propietario_id": uuid4(),
        "direccion": "Calle 10 # 20-30",
        "barrio": "El Poblado",
        "ciudad": "Medellin",
        "tipo": "apartamento",
        "area_m2": Decimal("65.5"),
        "habitaciones": 2,
        "banos": 2,
        "valor_mensual": Decimal("1500000"),
        "descripcion": "Apartamento amoblado cerca al metro",
        "fotos": [_build_foto_para_publicar(es_principal=True)],
    }
    kwargs.update(overrides)
    return PublicarInmuebleCommand(**kwargs)  # type: ignore[arg-type]


class TestPublicarInmuebleSuccess:
    async def test_should_create_inmueble_with_estado_disponible_and_upload_fotos_via_storage(
        self,
        fake_repository: FakeInmuebleRepository,
        fake_storage: FakeStoragePort,
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        command = _valid_command(
            propietario_id=propietario_id,
            fotos=[
                _build_foto_para_publicar(es_principal=True),
                _build_foto_para_publicar(es_principal=False),
            ],
        )

        # Act
        inmueble = await publicar_inmueble(
            command, repository=fake_repository, storage=fake_storage
        )

        # Assert
        assert inmueble.id is not None
        assert inmueble.estado == EstadoInmueble.DISPONIBLE
        assert inmueble.propietario_id == propietario_id
        assert len(inmueble.fotos) == 2
        assert len(fake_storage.subir_foto_calls) == 2
        assert len(fake_repository.guardar_calls) == 1
        assert all(
            foto.url_storage.startswith("https://fake-storage.test/") for foto in inmueble.fotos
        )


class TestPublicarInmuebleWithAgente:
    """Task 3.1 of `openspec/changes/hu-002/tasks.md`: `agente_id` is an
    optional field on `PublicarInmuebleCommand` (design.md decisión 2/4) —
    when the caller is an agente publishing on behalf of a propietario, the
    resulting `Inmueble` must carry that `agente_id`."""

    async def test_should_assign_agente_id_to_created_inmueble_when_command_has_it(
        self,
        fake_repository: FakeInmuebleRepository,
        fake_storage: FakeStoragePort,
    ) -> None:
        # Arrange
        agente_id = uuid4()
        command = _valid_command(agente_id=agente_id)

        # Act
        inmueble = await publicar_inmueble(
            command, repository=fake_repository, storage=fake_storage
        )

        # Assert
        assert inmueble.agente_id == agente_id

    async def test_should_leave_agente_id_none_when_command_does_not_provide_it(
        self,
        fake_repository: FakeInmuebleRepository,
        fake_storage: FakeStoragePort,
    ) -> None:
        # Arrange
        command = _valid_command()

        # Act
        inmueble = await publicar_inmueble(
            command, repository=fake_repository, storage=fake_storage
        )

        # Assert
        assert inmueble.agente_id is None


class TestPublicarInmuebleValidationFailures:
    async def test_should_propagate_domain_validation_error_when_valor_mensual_is_invalid(
        self,
        fake_repository: FakeInmuebleRepository,
        fake_storage: FakeStoragePort,
    ) -> None:
        # Arrange
        command = _valid_command(valor_mensual=Decimal("0"))

        # Act / Assert
        with pytest.raises(DomainValidationError):
            await publicar_inmueble(command, repository=fake_repository, storage=fake_storage)

        assert fake_repository.guardar_calls == []

    async def test_should_propagate_domain_validation_error_and_not_persist_when_no_fotos_provided(
        self,
        fake_repository: FakeInmuebleRepository,
        fake_storage: FakeStoragePort,
    ) -> None:
        # Arrange
        command = _valid_command(fotos=[])

        # Act / Assert
        with pytest.raises(DomainValidationError):
            await publicar_inmueble(command, repository=fake_repository, storage=fake_storage)

        assert fake_repository.guardar_calls == []
