"""Unit tests for the `editar_inmueble` use case
(`inmuebles/application/editar_inmueble.py`).

Covers tasks 3.3-3.4 of `openspec/changes/hu-001/tasks.md` and the
"Edición de inmueble publicado" requirement of
`openspec/changes/hu-001/specs/inmuebles/spec.md`.

TDD Red phase: `inmuebles/application/editar_inmueble.py` does not exist yet,
so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (tasks 4.2, 4.5). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `EditarInmuebleCommand`: a plain dataclass with `inmueble_id: UUID`,
  `propietario_id: UUID` (the caller's id, extracted from the JWT per
  design.md decisión 5 — NOT trusted from the entity) and the full set of
  editable data fields (`direccion`, `barrio`, `ciudad`, `tipo`, `area_m2`,
  `habitaciones`, `banos`, `valor_mensual`, `descripcion`). Editing `fotos`
  is out of scope for this use case/spec.
- `editar_inmueble(command, *, repository) -> Inmueble`: an async function
  that:
  1. Loads the `Inmueble` via `repository.obtener_por_id(command.inmueble_id)`.
  2. Raises `InmuebleNoEncontrado` when it doesn't exist.
  3. Raises `PropietarioInvalido` when `command.propietario_id` does not
     match the loaded `Inmueble.propietario_id` — and MUST NOT call
     `repository.actualizar` in that case.
  4. Otherwise applies every field from the command to the entity and
     persists it via `repository.actualizar(...)`, returning the updated
     instance.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from inmuebles.application.editar_inmueble import EditarInmuebleCommand, editar_inmueble
from inmuebles.domain.exceptions import PropietarioInvalido
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import Inmueble
from shared.domain.exceptions import DomainValidationError
from tests.inmuebles.application.conftest import FakeInmuebleRepository


def _build_existing_inmueble(*, propietario_id: object | None = None) -> Inmueble:
    return Inmueble.crear(
        propietario_id=propietario_id or uuid4(),
        direccion="Calle 10 # 20-30",
        barrio="El Poblado",
        ciudad="Medellin",
        tipo="apartamento",
        area_m2=Decimal("65.5"),
        habitaciones=2,
        banos=2,
        valor_mensual=Decimal("1500000"),
        descripcion="Apartamento amoblado cerca al metro",
        fotos=[
            FotoInmueble(
                url_storage="https://storage.example.com/inmuebles/fotos/1.jpg",
                storage_key="inmuebles/fotos/1.jpg",
                orden=1,
                es_principal=True,
            )
        ],
    )


def _edit_command(*, inmueble_id: object, propietario_id: object) -> EditarInmuebleCommand:
    return EditarInmuebleCommand(
        inmueble_id=inmueble_id,  # type: ignore[arg-type]
        propietario_id=propietario_id,  # type: ignore[arg-type]
        direccion="Carrera 50 # 10-20",
        barrio="Laureles",
        ciudad="Medellin",
        tipo="apartamento",
        area_m2=Decimal("70.0"),
        habitaciones=3,
        banos=2,
        valor_mensual=Decimal("1800000"),
        descripcion="Renovado, cerca a parques",
    )


class TestEditarInmuebleWhenPropietarioOwnsIt:
    async def test_should_update_inmueble_data_when_propietario_id_matches_owner(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        existing = fake_repository.seed(_build_existing_inmueble(propietario_id=propietario_id))
        assert existing.id is not None
        command = _edit_command(inmueble_id=existing.id, propietario_id=propietario_id)

        # Act
        updated = await editar_inmueble(command, repository=fake_repository)

        # Assert
        assert updated.id == existing.id
        assert updated.direccion == command.direccion
        assert updated.barrio == command.barrio
        assert updated.ciudad == command.ciudad
        assert updated.area_m2 == command.area_m2
        assert updated.habitaciones == command.habitaciones
        assert updated.banos == command.banos
        assert updated.valor_mensual == command.valor_mensual
        assert updated.descripcion == command.descripcion
        assert len(fake_repository.actualizar_calls) == 1


class TestEditarInmuebleWhenPropietarioDoesNotOwnIt:
    async def test_should_raise_propietario_invalido_and_not_persist_when_propietario_mismatches(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        owner_id = uuid4()
        other_propietario_id = uuid4()
        existing = fake_repository.seed(_build_existing_inmueble(propietario_id=owner_id))
        assert existing.id is not None
        original_direccion = existing.direccion
        command = _edit_command(inmueble_id=existing.id, propietario_id=other_propietario_id)

        # Act / Assert
        with pytest.raises(PropietarioInvalido):
            await editar_inmueble(command, repository=fake_repository)

        assert fake_repository.actualizar_calls == []
        stored = await fake_repository.obtener_por_id(existing.id)
        assert stored is not None
        assert stored.direccion == original_direccion


class TestEditarInmuebleWhenDataViolatesInvariants:
    """Guards against the gap where `editar_inmueble` applied `command`'s
    fields to the `Inmueble` by direct assignment without re-validating the
    same invariants `Inmueble.crear` enforces — allowing e.g.
    `valor_mensual=0` through unrejected. `editar_inmueble` must propagate
    `DomainValidationError` and must NOT call `repository.actualizar` in that
    case."""

    async def test_should_raise_domain_validation_error_and_not_persist_when_valor_mensual_is_zero(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        existing = fake_repository.seed(_build_existing_inmueble(propietario_id=propietario_id))
        assert existing.id is not None
        original_valor_mensual = existing.valor_mensual
        command = _edit_command(inmueble_id=existing.id, propietario_id=propietario_id)
        command.valor_mensual = Decimal("0")

        # Act / Assert
        with pytest.raises(DomainValidationError):
            await editar_inmueble(command, repository=fake_repository)

        assert fake_repository.actualizar_calls == []
        stored = await fake_repository.obtener_por_id(existing.id)
        assert stored is not None
        assert stored.valor_mensual == original_valor_mensual
