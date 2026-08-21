"""Unit tests for the `listar_mis_inmuebles` use case
(`inmuebles/application/listar_mis_inmuebles.py`).

Covers tasks 3.8-3.9 of `openspec/changes/hu-001/tasks.md` and the
"Listado de inmuebles propios" requirement of
`openspec/changes/hu-001/specs/inmuebles/spec.md`.

TDD Red phase: `inmuebles/application/listar_mis_inmuebles.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (tasks 4.4, 4.5). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `ListarMisInmueblesCommand`: a plain dataclass with a single field,
  `propietario_id: UUID` (extracted from the JWT, per design.md decisión 5).
- `listar_mis_inmuebles(command, *, repository) -> list[Inmueble]`: an async
  function that delegates directly to
  `repository.listar_por_propietario(command.propietario_id)` — it must NOT
  filter or paginate on its own; filtering by owner is the repository's
  responsibility (`InmuebleRepositoryPort.listar_por_propietario`). Every
  returned `Inmueble` carries its current `estado` as-is (no extra mapping
  needed at this layer).
"""

from decimal import Decimal
from uuid import uuid4

from inmuebles.application.listar_mis_inmuebles import (
    ListarMisInmueblesCommand,
    listar_mis_inmuebles,
)
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble
from tests.inmuebles.application.conftest import FakeInmuebleRepository


def _build_inmueble(*, propietario_id: object, estado: EstadoInmueble) -> Inmueble:
    inmueble = Inmueble.crear(
        propietario_id=propietario_id,  # type: ignore[arg-type]
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


class TestListarMisInmueblesWithOwnedInmuebles:
    async def test_should_return_only_inmuebles_owned_by_requested_propietario_with_current_estado(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        otro_propietario_id = uuid4()

        disponible = fake_repository.seed(
            _build_inmueble(propietario_id=propietario_id, estado=EstadoInmueble.DISPONIBLE)
        )
        oculto = fake_repository.seed(
            _build_inmueble(propietario_id=propietario_id, estado=EstadoInmueble.OCULTO)
        )
        fake_repository.seed(
            _build_inmueble(propietario_id=otro_propietario_id, estado=EstadoInmueble.DISPONIBLE)
        )

        command = ListarMisInmueblesCommand(propietario_id=propietario_id)

        # Act
        result = await listar_mis_inmuebles(command, repository=fake_repository)

        # Assert
        assert {inmueble.id for inmueble in result} == {disponible.id, oculto.id}
        assert all(inmueble.propietario_id == propietario_id for inmueble in result)
        estados_by_id = {inmueble.id: inmueble.estado for inmueble in result}
        assert estados_by_id[disponible.id] == EstadoInmueble.DISPONIBLE
        assert estados_by_id[oculto.id] == EstadoInmueble.OCULTO


class TestListarMisInmueblesWithoutOwnedInmuebles:
    async def test_should_return_empty_list_when_propietario_has_no_inmuebles(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        fake_repository.seed(
            _build_inmueble(propietario_id=uuid4(), estado=EstadoInmueble.DISPONIBLE)
        )
        command = ListarMisInmueblesCommand(propietario_id=propietario_id)

        # Act
        result = await listar_mis_inmuebles(command, repository=fake_repository)

        # Assert
        assert result == []
