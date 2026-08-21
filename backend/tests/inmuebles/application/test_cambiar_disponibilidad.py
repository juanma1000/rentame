"""Unit tests for the `cambiar_disponibilidad` use case
(`inmuebles/application/cambiar_disponibilidad.py`).

Covers tasks 3.5-3.7 of `openspec/changes/hu-001/tasks.md`, the
"Despublicación temporal del inmueble" and "Transición automática a no
disponible" requirements of `openspec/changes/hu-001/specs/inmuebles/spec.md`,
and `design.md` decisión 4: `cambiar_disponibilidad` is a single, synchronous,
idempotent application method — not an event listener — reused both by the
propietario-facing despublicar/republicar flow and by the future
`arrendamiento` use case (which has no "requesting propietario" concept at
all).

TDD Red phase: `inmuebles/application/cambiar_disponibilidad.py` does not
exist yet, so every test here is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (tasks 4.3, 4.5). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `CambiarDisponibilidadCommand`: a plain dataclass with `inmueble_id: UUID`,
  `nuevo_estado: EstadoInmueble`, and `propietario_id: UUID | None = None`.
  `propietario_id` is `None` when the caller is a system/internal operation
  (e.g. the future `arrendamiento` use case marking `NO_DISPONIBLE`) — in
  that case ownership is NOT checked. When `propietario_id` is provided (the
  propietario-facing despublicar/republicar endpoint), it MUST match the
  loaded `Inmueble.propietario_id`.
- `cambiar_disponibilidad(command, *, repository) -> Inmueble`: an async
  function that:
  1. Loads the `Inmueble` via `repository.obtener_por_id(command.inmueble_id)`.
  2. Raises `InmuebleNoEncontrado` when it doesn't exist.
  3. Raises `PropietarioInvalido` when `command.propietario_id` is not
     `None` and doesn't match the entity's owner.
  4. Maps `command.nuevo_estado` to the corresponding `Inmueble` transition
     method (`EstadoInmueble.OCULTO` -> `despublicar()`,
     `EstadoInmueble.DISPONIBLE` -> `republicar()`,
     `EstadoInmueble.NO_DISPONIBLE` -> `marcar_no_disponible()`) — it must
     NOT reimplement the transition logic itself.
  5. Persists via `repository.actualizar(...)` and returns the updated
     instance.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from inmuebles.application.cambiar_disponibilidad import (
    CambiarDisponibilidadCommand,
    cambiar_disponibilidad,
)
from inmuebles.domain.exceptions import InmuebleNoEncontrado
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
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


class TestCambiarDisponibilidadByOwningPropietario:
    async def test_should_change_estado_to_oculto_and_back_to_disponible_when_invoked_by_owner(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        existing = fake_repository.seed(_build_existing_inmueble(propietario_id=propietario_id))
        assert existing.id is not None

        # Act: despublicar
        despublicado = await cambiar_disponibilidad(
            CambiarDisponibilidadCommand(
                inmueble_id=existing.id,
                nuevo_estado=EstadoInmueble.OCULTO,
                propietario_id=propietario_id,
            ),
            repository=fake_repository,
        )

        # Assert
        assert despublicado.estado == EstadoInmueble.OCULTO

        # Act: republicar
        republicado = await cambiar_disponibilidad(
            CambiarDisponibilidadCommand(
                inmueble_id=existing.id,
                nuevo_estado=EstadoInmueble.DISPONIBLE,
                propietario_id=propietario_id,
            ),
            repository=fake_repository,
        )

        # Assert
        assert republicado.estado == EstadoInmueble.DISPONIBLE
        assert len(fake_repository.actualizar_calls) == 2


class TestCambiarDisponibilidadAsSystemOperation:
    async def test_should_change_estado_to_no_disponible_when_invoked_without_propietario_id(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange: simulates the future `arrendamiento` use case, which has
        # no "requesting propietario" concept and therefore omits it.
        existing = fake_repository.seed(_build_existing_inmueble())
        assert existing.id is not None

        # Act
        updated = await cambiar_disponibilidad(
            CambiarDisponibilidadCommand(
                inmueble_id=existing.id,
                nuevo_estado=EstadoInmueble.NO_DISPONIBLE,
            ),
            repository=fake_repository,
        )

        # Assert
        assert updated.estado == EstadoInmueble.NO_DISPONIBLE
        assert len(fake_repository.actualizar_calls) == 1


class TestCambiarDisponibilidadInmuebleNotFound:
    async def test_should_raise_inmueble_no_encontrado_when_inmueble_id_does_not_exist(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        nonexistent_id = uuid4()

        # Act / Assert
        with pytest.raises(InmuebleNoEncontrado):
            await cambiar_disponibilidad(
                CambiarDisponibilidadCommand(
                    inmueble_id=nonexistent_id,
                    nuevo_estado=EstadoInmueble.NO_DISPONIBLE,
                ),
                repository=fake_repository,
            )

        assert fake_repository.actualizar_calls == []
