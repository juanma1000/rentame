"""Unit tests for the `SolicitudIngreso` entity
(`agencias/domain/solicitud_ingreso.py`).

Pure domain tests: no database, no HTTP. They express the "Ingreso a una
agencia existente requiere aprobación" requirement of
`openspec/changes/hu-007/specs/agencias/spec.md` (tasks 1.8-1.9 of
`openspec/changes/hu-007/tasks.md`).

TDD Red phase: `agencias/domain/solicitud_ingreso.py` does not exist yet, so
every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 2.3). This file defines, by
construction, the contract the implementation must satisfy:

- `SolicitudIngreso.crear(*, agencia_id, agente_id)` is a factory
  classmethod that always starts the entity in
  `EstadoSolicitudIngreso.PENDIENTE`, with `id is None` (assigned later by
  the repository), same pattern as `Inmueble.crear`.
- `aprobar()` transitions `PENDIENTE -> APROBADA`. Calling it again from
  `APROBADA` raises `shared.domain.exceptions.DomainValidationError` and
  leaves `estado` unchanged ("¿quién aprobó y si el que aprueba es miembro
  de la agencia?" is validated by the `aprobar_ingreso` use case, task 3.6,
  not by this entity method).
"""

import uuid

import pytest

from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso, SolicitudIngreso
from shared.domain.exceptions import DomainValidationError


def _build_solicitud(**overrides: object) -> SolicitudIngreso:
    kwargs: dict[str, object] = {
        "agencia_id": uuid.uuid4(),
        "agente_id": uuid.uuid4(),
    }
    kwargs.update(overrides)
    return SolicitudIngreso.crear(**kwargs)


class TestSolicitudIngresoCrear:
    def test_should_create_solicitud_in_pendiente_state_when_data_is_valid(self) -> None:
        # Arrange
        agencia_id = uuid.uuid4()
        agente_id = uuid.uuid4()

        # Act
        solicitud = SolicitudIngreso.crear(agencia_id=agencia_id, agente_id=agente_id)

        # Assert
        assert solicitud.estado == EstadoSolicitudIngreso.PENDIENTE
        assert solicitud.agencia_id == agencia_id
        assert solicitud.agente_id == agente_id
        assert solicitud.id is None


class TestSolicitudIngresoAprobar:
    def test_should_change_estado_to_aprobada_when_aprobar_is_called_from_pendiente(
        self,
    ) -> None:
        # Arrange
        solicitud = _build_solicitud()
        assert solicitud.estado == EstadoSolicitudIngreso.PENDIENTE

        # Act
        solicitud.aprobar()

        # Assert
        assert solicitud.estado == EstadoSolicitudIngreso.APROBADA

    def test_should_raise_domain_validation_error_when_aprobar_is_called_from_aprobada(
        self,
    ) -> None:
        # Arrange
        solicitud = _build_solicitud()
        solicitud.aprobar()
        assert solicitud.estado == EstadoSolicitudIngreso.APROBADA

        # Act / Assert
        with pytest.raises(DomainValidationError):
            solicitud.aprobar()
        assert solicitud.estado == EstadoSolicitudIngreso.APROBADA
