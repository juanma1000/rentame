"""Unit tests for the `RelacionAgenciaPropietario` entity
(`agencias/domain/relacion_agencia_propietario.py`).

Pure domain tests: no database, no HTTP. They express the state-machine
rules from the "Relación agencia-propietario iniciada por el propietario",
"Máximo una agencia activa por propietario", "Revocación de la relación
agencia-propietario por el propietario" and "Agente responsable reasignable"
requirements of `openspec/changes/hu-007/specs/agencias/spec.md` (tasks
1.2-1.7 of `openspec/changes/hu-007/tasks.md`).

TDD Red phase: `agencias/domain/relacion_agencia_propietario.py` does not
exist yet, so every test here is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 2.2). This file defines, by
construction, the contract the implementation must satisfy:

- `RelacionAgenciaPropietario.crear(*, agencia_id, propietario_id)` is a
  factory classmethod that always starts the entity in
  `EstadoRelacion.PENDIENTE`, with `agente_responsable_id is None` and
  `id is None` (assigned later by the repository), same pattern as
  `Inmueble.crear`.
- `activar()` transitions `PENDIENTE -> ACTIVA`. Calling it from any other
  state raises `shared.domain.exceptions.DomainValidationError` and leaves
  `estado` unchanged.
- `revocar()` transitions `ACTIVA -> REVOCADA`. Calling it from any other
  state raises `DomainValidationError` and leaves `estado` unchanged.
- `reasignar_responsable(nuevo_agente_id)` overwrites
  `agente_responsable_id` in place, without touching `estado` (reassignment
  is traceability-only, per design.md decisión and the spec's "Agente
  responsable reasignable" requirement — authorization checks such as
  "is the new agent a member of this same agency" belong to the
  `reasignar_responsable` use case, task 3.18, not to this entity method).
"""

import uuid

import pytest

from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from shared.domain.exceptions import DomainValidationError


def _build_relacion(**overrides: object) -> RelacionAgenciaPropietario:
    kwargs: dict[str, object] = {
        "agencia_id": uuid.uuid4(),
        "propietario_id": uuid.uuid4(),
    }
    kwargs.update(overrides)
    return RelacionAgenciaPropietario.crear(**kwargs)


class TestRelacionAgenciaPropietarioCrear:
    def test_should_create_relacion_in_pendiente_state_when_data_is_valid(self) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        propietario_id = uuid.uuid4()

        # Act
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia_id, propietario_id=propietario_id
        )

        # Assert
        assert relacion.estado == EstadoRelacion.PENDIENTE
        assert relacion.agencia_id == agencia_id
        assert relacion.propietario_id == propietario_id
        assert relacion.agente_responsable_id is None
        assert relacion.id is None


class TestRelacionAgenciaPropietarioActivar:
    def test_should_change_estado_to_activa_when_activar_is_called_from_pendiente(self) -> None:
        # Arrange
        relacion = _build_relacion()
        assert relacion.estado == EstadoRelacion.PENDIENTE

        # Act
        relacion.activar()

        # Assert
        assert relacion.estado == EstadoRelacion.ACTIVA

    def test_should_raise_domain_validation_error_when_activar_is_called_from_activa(
        self,
    ) -> None:
        # Arrange
        relacion = _build_relacion()
        relacion.activar()
        assert relacion.estado == EstadoRelacion.ACTIVA

        # Act / Assert
        with pytest.raises(DomainValidationError):
            relacion.activar()
        assert relacion.estado == EstadoRelacion.ACTIVA

    def test_should_raise_domain_validation_error_when_activar_is_called_from_revocada(
        self,
    ) -> None:
        # Arrange
        relacion = _build_relacion()
        relacion.activar()
        relacion.revocar()
        assert relacion.estado == EstadoRelacion.REVOCADA

        # Act / Assert
        with pytest.raises(DomainValidationError):
            relacion.activar()
        assert relacion.estado == EstadoRelacion.REVOCADA


class TestRelacionAgenciaPropietarioRevocar:
    def test_should_change_estado_to_revocada_when_revocar_is_called_from_activa(self) -> None:
        # Arrange
        relacion = _build_relacion()
        relacion.activar()
        assert relacion.estado == EstadoRelacion.ACTIVA

        # Act
        relacion.revocar()

        # Assert
        assert relacion.estado == EstadoRelacion.REVOCADA

    def test_should_raise_domain_validation_error_when_revocar_is_called_from_pendiente(
        self,
    ) -> None:
        # Arrange
        relacion = _build_relacion()
        assert relacion.estado == EstadoRelacion.PENDIENTE

        # Act / Assert
        with pytest.raises(DomainValidationError):
            relacion.revocar()
        assert relacion.estado == EstadoRelacion.PENDIENTE

    def test_should_raise_domain_validation_error_when_revocar_is_called_from_revocada(
        self,
    ) -> None:
        # Arrange
        relacion = _build_relacion()
        relacion.activar()
        relacion.revocar()
        assert relacion.estado == EstadoRelacion.REVOCADA

        # Act / Assert
        with pytest.raises(DomainValidationError):
            relacion.revocar()
        assert relacion.estado == EstadoRelacion.REVOCADA


class TestRelacionAgenciaPropietarioReasignarResponsable:
    def test_should_update_agente_responsable_id_without_changing_estado(self) -> None:
        # Arrange
        relacion = _build_relacion()
        relacion.activar()
        primer_responsable = uuid.uuid4()
        relacion.reasignar_responsable(primer_responsable)
        assert relacion.agente_responsable_id == primer_responsable
        estado_antes = relacion.estado

        # Act
        nuevo_responsable = uuid.uuid4()
        relacion.reasignar_responsable(nuevo_responsable)

        # Assert
        assert relacion.agente_responsable_id == nuevo_responsable
        assert relacion.estado == estado_antes
