"""Unit tests for the `obtener_inmueble_publico` use case
(`inmuebles/application/obtener_inmueble_publico.py`).

Covers `openspec/changes/hu-003/specs/inmuebles/spec.md` requirement
"Detalle público de un inmueble disponible" and `design.md` decisión 1 of
that same change.

TDD Red phase: `inmuebles/application/obtener_inmueble_publico.py` does not
exist yet, so every test here is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it. This file fixes, by construction, the
contract `backend-expert` must satisfy:

- `ObtenerInmueblePublicoCommand`: a plain dataclass with a single field,
  `inmueble_id: UUID`.
- `obtener_inmueble_publico(command, *, repository) -> Inmueble | None`: an
  async function that calls `repository.obtener_por_id(command.inmueble_id)`
  and then validates `estado == EstadoInmueble.DISPONIBLE` itself (no new
  repository method needed for this use case, per design.md decisión 1) —
  returning the `Inmueble` only when it exists AND is `disponible`.
- Returns `None` (never raises) when `inmueble_id` does not match any
  `Inmueble` in the repository.
- Returns `None` (never raises) when the `Inmueble` exists but its `estado`
  is `oculto` or `no_disponible` — this use case must never leak the
  existence/data of a non-`disponible` inmueble through its return value.
"""

from decimal import Decimal
from uuid import uuid4

from inmuebles.application.obtener_inmueble_publico import (
    ObtenerInmueblePublicoCommand,
    obtener_inmueble_publico,
)
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from tests.inmuebles.application.conftest import FakeInmuebleRepository


def _build_inmueble(*, estado: EstadoInmueble) -> Inmueble:
    inmueble = Inmueble.crear(
        propietario_id=uuid4(),
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
    inmueble.estado = estado
    return inmueble


class TestObtenerInmueblePublicoWithDisponibleInmueble:
    async def test_should_return_inmueble_when_it_exists_and_is_disponible(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        disponible = fake_repository.seed(_build_inmueble(estado=EstadoInmueble.DISPONIBLE))
        command = ObtenerInmueblePublicoCommand(inmueble_id=disponible.id)

        # Act
        result = await obtener_inmueble_publico(command, repository=fake_repository)

        # Assert
        assert result is not None
        assert result.id == disponible.id
        assert result.estado == EstadoInmueble.DISPONIBLE


class TestObtenerInmueblePublicoWithUnknownId:
    async def test_should_return_none_when_inmueble_id_does_not_exist(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        command = ObtenerInmueblePublicoCommand(inmueble_id=uuid4())

        # Act
        result = await obtener_inmueble_publico(command, repository=fake_repository)

        # Assert
        assert result is None


class TestObtenerInmueblePublicoWithNonDisponibleInmueble:
    async def test_should_return_none_when_inmueble_is_oculto(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        oculto = fake_repository.seed(_build_inmueble(estado=EstadoInmueble.OCULTO))
        command = ObtenerInmueblePublicoCommand(inmueble_id=oculto.id)

        # Act
        result = await obtener_inmueble_publico(command, repository=fake_repository)

        # Assert
        assert result is None

    async def test_should_return_none_when_inmueble_is_no_disponible(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        no_disponible = fake_repository.seed(
            _build_inmueble(estado=EstadoInmueble.NO_DISPONIBLE)
        )
        command = ObtenerInmueblePublicoCommand(inmueble_id=no_disponible.id)

        # Act
        result = await obtener_inmueble_publico(command, repository=fake_repository)

        # Assert
        assert result is None
