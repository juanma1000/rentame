"""Unit tests for the `PolizaArrendamiento` aggregate
(`seguro_arrendamiento/domain/poliza_arrendamiento.py`).

Pure domain tests: no database, no HTTP. They express the "Resultado
modelado como póliza con estado propio" requirement of
`openspec/changes/seguro-arrendamiento-inquilino/specs/seguro-arrendamiento/spec.md`
(task 1.1 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`).

TDD Red phase: `seguro_arrendamiento/domain/poliza_arrendamiento.py` does not
exist yet, so this test is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 1.2). This file fixes, by
construction, the contract the implementation must satisfy:

- `EstadoPoliza` enum: `PENDIENTE`, `APROBADA`, `RECHAZADA`, `ACTIVA`,
  `VENCIDA`.
- `PolizaArrendamiento.solicitar(*, usuario_id)` is a factory classmethod
  that returns a new instance in `EstadoPoliza.PENDIENTE`, with `id is None`
  (assigned by the repository on insert, same pattern as
  `ValidacionIdentidad.iniciar`).
- `.aprobar(*, prima_mensual, vigencia_desde, vigencia_hasta,
  referencia_externa)` transitions `PENDIENTE` -> `APROBADA` and stores the
  fields.
- `.rechazar(*, referencia_externa)` transitions `PENDIENTE` -> `RECHAZADA`.
- `.activar()` transitions `APROBADA` -> `ACTIVA`. Raises
  `seguro_arrendamiento.domain.exceptions.PolizaRechazadaNoPuedeActivarse`
  when called on a `RECHAZADA` póliza — the invariant "póliza rechazada no
  puede activarse".
- `.vencer()` transitions `ACTIVA` -> `VENCIDA`.
"""

import uuid
from datetime import date

import pytest

from seguro_arrendamiento.domain.exceptions import PolizaRechazadaNoPuedeActivarse
from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza, PolizaArrendamiento


class TestPolizaArrendamientoSolicitar:
    def test_should_create_pendiente_poliza(self) -> None:
        # Arrange
        usuario_id = uuid.uuid4()

        # Act
        poliza = PolizaArrendamiento.solicitar(usuario_id=usuario_id)

        # Assert
        assert poliza.usuario_id == usuario_id
        assert poliza.estado == EstadoPoliza.PENDIENTE
        assert poliza.id is None
        assert poliza.prima_mensual is None
        assert poliza.referencia_externa is None


class TestPolizaArrendamientoAprobarRechazar:
    def test_aprobar_sets_estado_aprobada_and_fields(self) -> None:
        # Arrange
        poliza = PolizaArrendamiento.solicitar(usuario_id=uuid.uuid4())

        # Act
        poliza.aprobar(
            prima_mensual=50000.0,
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2027, 1, 1),
            referencia_externa="ext-1",
        )

        # Assert
        assert poliza.estado == EstadoPoliza.APROBADA
        assert poliza.prima_mensual == 50000.0
        assert poliza.vigencia_desde == date(2026, 1, 1)
        assert poliza.vigencia_hasta == date(2027, 1, 1)
        assert poliza.referencia_externa == "ext-1"

    def test_rechazar_sets_estado_rechazada(self) -> None:
        # Arrange
        poliza = PolizaArrendamiento.solicitar(usuario_id=uuid.uuid4())

        # Act
        poliza.rechazar(referencia_externa="ext-2")

        # Assert
        assert poliza.estado == EstadoPoliza.RECHAZADA
        assert poliza.referencia_externa == "ext-2"


class TestPolizaArrendamientoTransicionesVigencia:
    def test_activar_transitions_aprobada_to_activa(self) -> None:
        # Arrange
        poliza = PolizaArrendamiento.solicitar(usuario_id=uuid.uuid4())
        poliza.aprobar(
            prima_mensual=50000.0,
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2027, 1, 1),
            referencia_externa="ext-1",
        )

        # Act
        poliza.activar()

        # Assert
        assert poliza.estado == EstadoPoliza.ACTIVA

    def test_vencer_transitions_activa_to_vencida(self) -> None:
        # Arrange
        poliza = PolizaArrendamiento.solicitar(usuario_id=uuid.uuid4())
        poliza.aprobar(
            prima_mensual=50000.0,
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2027, 1, 1),
            referencia_externa="ext-1",
        )
        poliza.activar()

        # Act
        poliza.vencer()

        # Assert
        assert poliza.estado == EstadoPoliza.VENCIDA

    def test_activar_raises_when_poliza_is_rechazada(self) -> None:
        # Arrange
        poliza = PolizaArrendamiento.solicitar(usuario_id=uuid.uuid4())
        poliza.rechazar(referencia_externa="ext-2")

        # Act / Assert
        with pytest.raises(PolizaRechazadaNoPuedeActivarse):
            poliza.activar()
