"""Unit tests for the `Inmueble` entity and `FotoInmueble` value object
(`inmuebles/domain/inmueble.py`, `inmuebles/domain/foto.py`).

Pure domain tests: no database, no HTTP, no storage adapter. They express the
validation rules and state-transition rules from
`openspec/changes/hu-001/specs/inmuebles/spec.md` and the "MAX_FOTOS_INMUEBLE"
decision from `openspec/changes/hu-001/design.md`.

TDD Red phase: `inmuebles/domain/inmueble.py` and `inmuebles/domain/foto.py`
do not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements them (tasks 2.1-2.4 of
`openspec/changes/hu-001/tasks.md`). This file defines, by construction, the
contract the implementation must satisfy:

- `Inmueble.crear(...)` is a factory classmethod: it validates all business
  rules up front and always returns an `Inmueble` with `estado ==
  EstadoInmueble.DISPONIBLE` (per "Estado inicial de la publicación").
  Invalid input raises `shared.domain.exceptions.DomainValidationError`.
- `FotoInmueble` is an immutable value object with `url_storage`,
  `storage_key`, `orden` and `es_principal`.
- `MAX_FOTOS_INMUEBLE` is a module-level constant (see design.md decision 2).
- State transitions are instance methods `despublicar()`, `republicar()` and
  `marcar_no_disponible()`, which mutate `estado` in place.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import MAX_FOTOS_INMUEBLE, EstadoInmueble, Inmueble
from shared.domain.exceptions import DomainValidationError


def _build_foto(orden: int = 1, *, es_principal: bool = False) -> FotoInmueble:
    return FotoInmueble(
        url_storage=f"https://storage.example.com/inmuebles/fotos/{orden}.jpg",
        storage_key=f"inmuebles/fotos/{orden}.jpg",
        orden=orden,
        es_principal=es_principal,
    )


def _build_fotos(count: int) -> list[FotoInmueble]:
    return [_build_foto(orden=n, es_principal=(n == 1)) for n in range(1, count + 1)]


def _valid_inmueble_kwargs(**overrides: object) -> dict[str, object]:
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
        "fotos": _build_fotos(1),
    }
    kwargs.update(overrides)
    return kwargs


class TestInmuebleCrear:
    def test_should_create_inmueble_with_estado_disponible_when_all_required_fields_are_valid(
        self,
    ) -> None:
        # Arrange
        propietario_id = uuid4()
        fotos = _build_fotos(3)
        kwargs = _valid_inmueble_kwargs(propietario_id=propietario_id, fotos=fotos)

        # Act
        inmueble = Inmueble.crear(**kwargs)

        # Assert
        assert inmueble.estado == EstadoInmueble.DISPONIBLE
        assert inmueble.propietario_id == propietario_id
        assert inmueble.direccion == kwargs["direccion"]
        assert inmueble.barrio == kwargs["barrio"]
        assert inmueble.ciudad == kwargs["ciudad"]
        assert inmueble.tipo == kwargs["tipo"]
        assert inmueble.area_m2 == kwargs["area_m2"]
        assert inmueble.habitaciones == kwargs["habitaciones"]
        assert inmueble.banos == kwargs["banos"]
        assert inmueble.valor_mensual == kwargs["valor_mensual"]
        assert inmueble.descripcion == kwargs["descripcion"]
        assert inmueble.fotos == fotos


class TestInmuebleCrearAgenteId:
    """`agente_id` (hu-002, design.md decisión 4) is an optional creation-time
    datum with no business validation attached — the domain only stores it,
    since agencia<->propietario authorization is resolved before reaching
    this factory (see `openspec/changes/hu-002/design.md`, Decisión 1)."""

    def test_should_assign_agente_id_when_provided(self) -> None:
        # Arrange
        agente_id = uuid4()
        kwargs = _valid_inmueble_kwargs(agente_id=agente_id)

        # Act
        inmueble = Inmueble.crear(**kwargs)

        # Assert
        assert inmueble.agente_id == agente_id

    def test_should_default_agente_id_to_none_when_not_provided(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs()

        # Act
        inmueble = Inmueble.crear(**kwargs)

        # Assert
        assert inmueble.agente_id is None


class TestInmuebleCrearValorMensualValidation:
    def test_should_raise_domain_validation_error_when_valor_mensual_is_zero(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(valor_mensual=Decimal("0"))

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)

    def test_should_raise_domain_validation_error_when_valor_mensual_is_negative(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(valor_mensual=Decimal("-100000"))

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)


class TestInmuebleCrearHabitacionesYBanosValidation:
    def test_should_raise_domain_validation_error_when_habitaciones_is_negative(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(habitaciones=-1)

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)

    def test_should_raise_domain_validation_error_when_banos_is_negative(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(banos=-1)

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)


class TestInmuebleCrearFotosValidation:
    def test_max_fotos_inmueble_constant_equals_ten(self) -> None:
        # Assert
        assert MAX_FOTOS_INMUEBLE == 10

    def test_should_raise_domain_validation_error_when_no_fotos_are_provided(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(fotos=[])

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)

    def test_should_raise_domain_validation_error_when_fotos_exceed_max_fotos_inmueble(
        self,
    ) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(fotos=_build_fotos(MAX_FOTOS_INMUEBLE + 1))

        # Act / Assert
        with pytest.raises(DomainValidationError):
            Inmueble.crear(**kwargs)

    def test_should_create_inmueble_when_fotos_count_is_at_min_boundary(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(fotos=_build_fotos(1))

        # Act
        inmueble = Inmueble.crear(**kwargs)

        # Assert
        assert len(inmueble.fotos) == 1

    def test_should_create_inmueble_when_fotos_count_is_at_max_boundary(self) -> None:
        # Arrange
        kwargs = _valid_inmueble_kwargs(fotos=_build_fotos(MAX_FOTOS_INMUEBLE))

        # Act
        inmueble = Inmueble.crear(**kwargs)

        # Assert
        assert len(inmueble.fotos) == MAX_FOTOS_INMUEBLE


class TestInmuebleActualizarDatos:
    """Tests for `Inmueble.actualizar_datos(...)`, the entity method that
    must apply an edit (`editar_inmueble` use case) while re-validating the
    same business invariants enforced by `Inmueble.crear` (`valor_mensual`
    strictly positive, `habitaciones`/`banos` non-negative). Without this
    method, `editar_inmueble` currently assigns fields directly and lets an
    invalid edit (e.g. `valor_mensual=0`) through unrejected."""

    def setup_method(self) -> None:
        self.inmueble = Inmueble.crear(**_valid_inmueble_kwargs())

    def test_should_raise_domain_validation_error_when_valor_mensual_is_zero(self) -> None:
        # Arrange
        nuevos_datos = _valid_inmueble_kwargs(valor_mensual=Decimal("0"))
        nuevos_datos.pop("propietario_id")
        nuevos_datos.pop("fotos")

        # Act / Assert
        with pytest.raises(DomainValidationError):
            self.inmueble.actualizar_datos(**nuevos_datos)

    def test_should_update_fields_when_new_data_is_valid(self) -> None:
        # Arrange
        nuevos_datos = _valid_inmueble_kwargs(
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
        nuevos_datos.pop("propietario_id")
        nuevos_datos.pop("fotos")

        # Act
        self.inmueble.actualizar_datos(**nuevos_datos)

        # Assert
        assert self.inmueble.direccion == nuevos_datos["direccion"]
        assert self.inmueble.barrio == nuevos_datos["barrio"]
        assert self.inmueble.ciudad == nuevos_datos["ciudad"]
        assert self.inmueble.tipo == nuevos_datos["tipo"]
        assert self.inmueble.area_m2 == nuevos_datos["area_m2"]
        assert self.inmueble.habitaciones == nuevos_datos["habitaciones"]
        assert self.inmueble.banos == nuevos_datos["banos"]
        assert self.inmueble.valor_mensual == nuevos_datos["valor_mensual"]
        assert self.inmueble.descripcion == nuevos_datos["descripcion"]


class TestInmuebleTransicionesEstado:
    def setup_method(self) -> None:
        self.inmueble = Inmueble.crear(**_valid_inmueble_kwargs())

    def test_should_change_estado_to_oculto_when_despublicar_is_called_from_disponible(
        self,
    ) -> None:
        # Arrange
        assert self.inmueble.estado == EstadoInmueble.DISPONIBLE

        # Act
        self.inmueble.despublicar()

        # Assert
        assert self.inmueble.estado == EstadoInmueble.OCULTO

    def test_should_change_estado_to_disponible_when_republicar_is_called_from_oculto(
        self,
    ) -> None:
        # Arrange
        self.inmueble.despublicar()
        assert self.inmueble.estado == EstadoInmueble.OCULTO

        # Act
        self.inmueble.republicar()

        # Assert
        assert self.inmueble.estado == EstadoInmueble.DISPONIBLE

    def test_should_change_estado_to_no_disponible_when_marcar_no_disponible_is_called(
        self,
    ) -> None:
        # Arrange
        assert self.inmueble.estado == EstadoInmueble.DISPONIBLE

        # Act
        self.inmueble.marcar_no_disponible()

        # Assert
        assert self.inmueble.estado == EstadoInmueble.NO_DISPONIBLE
