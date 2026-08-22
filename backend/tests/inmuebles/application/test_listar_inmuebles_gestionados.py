"""Unit tests for the `listar_inmuebles_gestionados` use case
(`inmuebles/application/listar_inmuebles_gestionados.py`).

Covers tasks 3.3-3.4 of `openspec/changes/hu-002/tasks.md` and the
"GET /inmuebles/gestionados" requirement described in `design.md` decisión 6
of `openspec/changes/hu-002/`.

TDD Red phase: `inmuebles/application/listar_inmuebles_gestionados.py` does
not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it. This file fixes,
by construction, the contract `backend-expert` must satisfy:

- `listar_inmuebles_gestionados(propietario_ids, *, repository) -> list[Inmueble]`:
  an async function whose first (positional) argument is a plain
  `list[UUID]` of already-resolved `propietario_id`s — NOT a command
  dataclass, and NOT an `agente_id` — per design.md decisión 6, the
  cross-domain resolution of "which propietarios does this agente's agencia
  manage" happens in the API layer, this use case only receives the result.
  It must delegate directly to a new repository method,
  `repository.listar_por_propietarios(propietario_ids)`, without
  re-filtering or re-implementing that lookup itself (same thin
  pass-through pattern as `listar_mis_inmuebles`).
- When `propietario_ids` is an empty list, it returns an empty list (no
  repository call is required to short-circuit this, but the repository
  fake here also honors it as an empty `WHERE ... IN ()`).
"""

from decimal import Decimal
from uuid import uuid4

from inmuebles.application.listar_inmuebles_gestionados import listar_inmuebles_gestionados
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


class TestListarInmueblesGestionadosWithResolvedPropietarioIds:
    async def test_should_return_inmuebles_of_every_requested_propietario_with_current_estado(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        propietario_a = uuid4()
        propietario_b = uuid4()
        propietario_no_gestionado = uuid4()

        inmueble_a = fake_repository.seed(
            _build_inmueble(propietario_id=propietario_a, estado=EstadoInmueble.DISPONIBLE)
        )
        inmueble_b = fake_repository.seed(
            _build_inmueble(propietario_id=propietario_b, estado=EstadoInmueble.OCULTO)
        )
        fake_repository.seed(
            _build_inmueble(
                propietario_id=propietario_no_gestionado, estado=EstadoInmueble.DISPONIBLE
            )
        )

        # Act
        result = await listar_inmuebles_gestionados(
            [propietario_a, propietario_b], repository=fake_repository
        )

        # Assert
        assert {inmueble.id for inmueble in result} == {inmueble_a.id, inmueble_b.id}
        estados_by_id = {inmueble.id: inmueble.estado for inmueble in result}
        assert estados_by_id[inmueble_a.id] == EstadoInmueble.DISPONIBLE
        assert estados_by_id[inmueble_b.id] == EstadoInmueble.OCULTO


class TestListarInmueblesGestionadosWithEmptyPropietarioIds:
    async def test_should_return_empty_list_when_propietario_ids_is_empty(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        fake_repository.seed(
            _build_inmueble(propietario_id=uuid4(), estado=EstadoInmueble.DISPONIBLE)
        )

        # Act
        result = await listar_inmuebles_gestionados([], repository=fake_repository)

        # Assert
        assert result == []
