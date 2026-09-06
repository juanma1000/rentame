"""Unit tests for the `ArrendamientoActivo` aggregate
(`firma_contrato/domain/arrendamiento_activo.py`).

Pure domain tests: no database, no HTTP. Express the "Contrato firmado crea
un arrendamiento activo" requirement of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(task 1.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

TDD Red phase: `firma_contrato/domain/arrendamiento_activo.py` does not
exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 1.4). This
file fixes, by construction, the contract the implementation must satisfy:

- `ArrendamientoActivo.crear(*, contrato)` is a factory
  classmethod that only succeeds when `contrato.estado ==
  EstadoContrato.FIRMADO` — raises
  `firma_contrato.domain.exceptions.ArrendamientoRequiereContratoFirmado`
  otherwise. Copies `usuario_id`/`poliza_id`/`contrato.id` from the given
  `contrato` and returns a new instance in `EstadoArrendamientoActivo.ACTIVO`
  with `id is None`.
"""

import uuid
from datetime import date

import pytest

from firma_contrato.domain.arrendamiento_activo import (
    ArrendamientoActivo,
    EstadoArrendamientoActivo,
)
from firma_contrato.domain.contrato import Contrato
from firma_contrato.domain.exceptions import ArrendamientoRequiereContratoFirmado


def _contrato_firmado() -> Contrato:
    contrato = Contrato.generar(
        usuario_id=uuid.uuid4(),
        poliza_id=uuid.uuid4(),
        inmueble_id=uuid.uuid4(),
        documento_referencia="contrato-texto-generado",
    )
    contrato.id = uuid.uuid4()
    contrato.enviar_a_firma(referencia_externa="ext-1")
    contrato.marcar_firmado()
    return contrato


class TestArrendamientoActivoCrear:
    def test_should_create_arrendamiento_activo_from_contrato_firmado(self) -> None:
        # Arrange
        contrato = _contrato_firmado()

        # Act
        arrendamiento = ArrendamientoActivo.crear(contrato=contrato)

        # Assert
        assert arrendamiento.usuario_id == contrato.usuario_id
        assert arrendamiento.poliza_id == contrato.poliza_id
        assert arrendamiento.contrato_id == contrato.id
        assert arrendamiento.inmueble_id == contrato.inmueble_id
        assert arrendamiento.estado == EstadoArrendamientoActivo.ACTIVO
        assert arrendamiento.fecha_inicio == date.today()
        assert arrendamiento.id is None

    def test_should_raise_when_contrato_is_not_firmado(self) -> None:
        # Arrange
        contrato = Contrato.generar(
            usuario_id=uuid.uuid4(),
            poliza_id=uuid.uuid4(),
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-texto-generado",
        )
        contrato.id = uuid.uuid4()

        # Act / Assert
        with pytest.raises(ArrendamientoRequiereContratoFirmado):
            ArrendamientoActivo.crear(contrato=contrato)
