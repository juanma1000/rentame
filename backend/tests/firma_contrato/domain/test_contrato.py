"""Unit tests for the `Contrato` aggregate
(`firma_contrato/domain/contrato.py`).

Pure domain tests: no database, no HTTP. Express the "Resultado modelado
como contrato con estado propio" requirement of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(task 1.1 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

TDD Red phase: `firma_contrato/domain/contrato.py` does not exist yet, so
every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 1.2). This file fixes, by
construction, the contract the implementation must satisfy:

- `EstadoContrato` enum: `BORRADOR`, `ENVIADO_A_FIRMA`, `FIRMADO`,
  `RECHAZADO`, `EXPIRADO`.
- `Contrato.generar(*, usuario_id, poliza_id, inmueble_id, documento_referencia)` is a
  factory classmethod returning a new instance in `EstadoContrato.BORRADOR`,
  with `id is None` (assigned by the repository on insert).
- `.enviar_a_firma(*, referencia_externa)` transitions `BORRADOR` ->
  `ENVIADO_A_FIRMA`.
- `.marcar_firmado()` transitions `ENVIADO_A_FIRMA` -> `FIRMADO`. Raises
  `firma_contrato.domain.exceptions.ContratoYaFirmado` when called on a
  contrato already `FIRMADO` — invariant "un contrato firmado no puede
  volver a un estado anterior".
- `.marcar_rechazado()` transitions `ENVIADO_A_FIRMA` -> `RECHAZADO`. Same
  invariant applies.
- `.marcar_expirado()` transitions `ENVIADO_A_FIRMA` -> `EXPIRADO`. Same
  invariant applies.
"""

import uuid

import pytest

from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.domain.exceptions import ContratoYaFirmado


class TestContratoGenerar:
    def test_should_create_borrador_contrato(self) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        poliza_id = uuid.uuid4()
        inmueble_id = uuid.uuid4()

        # Act
        contrato = Contrato.generar(
            usuario_id=usuario_id,
            poliza_id=poliza_id,
            inmueble_id=inmueble_id,
            documento_referencia="contrato-texto-generado",
        )

        # Assert
        assert contrato.usuario_id == usuario_id
        assert contrato.poliza_id == poliza_id
        assert contrato.inmueble_id == inmueble_id
        assert contrato.estado == EstadoContrato.BORRADOR
        assert contrato.id is None
        assert contrato.documento_referencia == "contrato-texto-generado"
        assert contrato.referencia_externa is None


class TestContratoTransiciones:
    def _contrato_borrador(self) -> Contrato:
        return Contrato.generar(
            usuario_id=uuid.uuid4(),
            poliza_id=uuid.uuid4(),
            inmueble_id=uuid.uuid4(),
            documento_referencia="contrato-texto-generado",
        )

    def test_enviar_a_firma_transitions_borrador_to_enviado_a_firma(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()

        # Act
        contrato.enviar_a_firma(referencia_externa="ext-1")

        # Assert
        assert contrato.estado == EstadoContrato.ENVIADO_A_FIRMA
        assert contrato.referencia_externa == "ext-1"

    def test_marcar_firmado_transitions_enviado_a_firma_to_firmado(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()
        contrato.enviar_a_firma(referencia_externa="ext-1")

        # Act
        contrato.marcar_firmado()

        # Assert
        assert contrato.estado == EstadoContrato.FIRMADO

    def test_marcar_rechazado_transitions_enviado_a_firma_to_rechazado(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()
        contrato.enviar_a_firma(referencia_externa="ext-1")

        # Act
        contrato.marcar_rechazado()

        # Assert
        assert contrato.estado == EstadoContrato.RECHAZADO

    def test_marcar_expirado_transitions_enviado_a_firma_to_expirado(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()
        contrato.enviar_a_firma(referencia_externa="ext-1")

        # Act
        contrato.marcar_expirado()

        # Assert
        assert contrato.estado == EstadoContrato.EXPIRADO

    def test_marcar_firmado_raises_when_already_firmado(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()
        contrato.enviar_a_firma(referencia_externa="ext-1")
        contrato.marcar_firmado()

        # Act / Assert
        with pytest.raises(ContratoYaFirmado):
            contrato.marcar_firmado()

    def test_enviar_a_firma_raises_when_already_firmado(self) -> None:
        # Arrange
        contrato = self._contrato_borrador()
        contrato.enviar_a_firma(referencia_externa="ext-1")
        contrato.marcar_firmado()

        # Act / Assert
        with pytest.raises(ContratoYaFirmado):
            contrato.enviar_a_firma(referencia_externa="ext-2")
