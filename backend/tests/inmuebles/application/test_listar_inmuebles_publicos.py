"""Unit tests for the `listar_inmuebles_publicos` use case
(`inmuebles/application/listar_inmuebles_publicos.py`).

Covers `openspec/changes/hu-003/specs/inmuebles/spec.md` requirement
"Listado público de inmuebles disponibles" and `design.md` decisiones 1-2 of
that same change.

TDD Red phase: `inmuebles/application/listar_inmuebles_publicos.py` does not
exist yet, so every test here is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it. This file fixes, by construction, the
contract `backend-expert` must satisfy:

- `listar_inmuebles_publicos(*, repository) -> list[Inmueble]`: an async
  function with no positional/command argument (no filters exist yet, per
  design.md's "Non-Goals") that delegates directly to
  `repository.listar_disponibles()` — same thin pass-through pattern already
  used by `listar_mis_inmuebles`/`listar_inmuebles_gestionados` — without
  re-filtering or re-implementing the `estado == EstadoInmueble.DISPONIBLE`
  check itself (that filter lives in the repository per design.md decisión
  2). Every returned `Inmueble` is therefore already guaranteed `disponible`.
- Returns an empty list (no exception) when no `Inmueble` is `disponible`.
"""

from decimal import Decimal
from uuid import uuid4

from inmuebles.application.listar_inmuebles_publicos import listar_inmuebles_publicos
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


class TestListarInmueblesPublicosWithMixedEstados:
    async def test_should_return_only_inmuebles_in_estado_disponible(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        disponible_1 = fake_repository.seed(_build_inmueble(estado=EstadoInmueble.DISPONIBLE))
        disponible_2 = fake_repository.seed(_build_inmueble(estado=EstadoInmueble.DISPONIBLE))
        fake_repository.seed(_build_inmueble(estado=EstadoInmueble.OCULTO))
        fake_repository.seed(_build_inmueble(estado=EstadoInmueble.NO_DISPONIBLE))

        # Act
        result = await listar_inmuebles_publicos(repository=fake_repository)

        # Assert
        assert {inmueble.id for inmueble in result} == {disponible_1.id, disponible_2.id}
        assert all(inmueble.estado == EstadoInmueble.DISPONIBLE for inmueble in result)


class TestListarInmueblesPublicosWithoutAnyDisponible:
    async def test_should_return_empty_list_when_no_inmueble_is_disponible(
        self, fake_repository: FakeInmuebleRepository
    ) -> None:
        # Arrange
        fake_repository.seed(_build_inmueble(estado=EstadoInmueble.OCULTO))
        fake_repository.seed(_build_inmueble(estado=EstadoInmueble.NO_DISPONIBLE))

        # Act
        result = await listar_inmuebles_publicos(repository=fake_repository)

        # Assert
        assert result == []
