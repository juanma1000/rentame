"""Unit tests for the `Pago` aggregate (`pagos/domain/pago.py`).

Pure domain tests: no database, no HTTP. Express the "Resultado modelado
como pago con estado propio" requirement of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md` (task 1.1 of
`openspec/changes/pago-mensual-renta/tasks.md`).

TDD Red phase: `pagos/domain/pago.py` does not exist yet, so every test
here is expected to fail with `ModuleNotFoundError` until `backend-expert`
implements it (task 1.2). This file fixes, by construction, the contract
the implementation must satisfy:

- `EstadoPago` enum: `PENDIENTE`, `COMPLETADO`, `FALLIDO`.
- `Pago.crear(*, arrendamiento_activo_id, monto, fecha_limite)` is a
  factory classmethod returning a new instance in `EstadoPago.PENDIENTE`,
  with `id is None` (assigned by the repository on insert).
- `.marcar_completado(*, referencia_externa)` transitions to `COMPLETADO`
  and sets `fecha_pago`.
- `.marcar_fallido(*, referencia_externa)` transitions to `FALLIDO`
  without setting `fecha_pago`.
- Once `COMPLETADO`, no further state transition is possible — calling any
  transition method again raises
  `pagos.domain.exceptions.PagoYaCompletado` (invariant: "un pago
  completado no puede volver a pendiente").
"""

import uuid
from datetime import date, timedelta

import pytest

from pagos.domain.exceptions import PagoYaCompletado
from pagos.domain.pago import EstadoPago, Pago


def _pago_pendiente() -> Pago:
    return Pago.crear(
        arrendamiento_activo_id=uuid.uuid4(),
        monto=1_500_000.0,
        fecha_limite=date.today() + timedelta(days=5),
    )


class TestPagoCrear:
    def test_should_create_pago_pendiente(self) -> None:
        # Arrange
        arrendamiento_activo_id = uuid.uuid4()
        fecha_limite = date.today() + timedelta(days=5)

        # Act
        pago = Pago.crear(
            arrendamiento_activo_id=arrendamiento_activo_id,
            monto=1_500_000.0,
            fecha_limite=fecha_limite,
        )

        # Assert
        assert pago.arrendamiento_activo_id == arrendamiento_activo_id
        assert pago.monto == 1_500_000.0
        assert pago.fecha_limite == fecha_limite
        assert pago.estado == EstadoPago.PENDIENTE
        assert pago.id is None
        assert pago.fecha_pago is None
        assert pago.referencia_externa is None


class TestPagoTransiciones:
    def test_marcar_completado_transitions_pendiente_to_completado(self) -> None:
        # Arrange
        pago = _pago_pendiente()

        # Act
        pago.marcar_completado(referencia_externa="ext-1")

        # Assert
        assert pago.estado == EstadoPago.COMPLETADO
        assert pago.referencia_externa == "ext-1"
        assert pago.fecha_pago is not None

    def test_marcar_fallido_transitions_pendiente_to_fallido(self) -> None:
        # Arrange
        pago = _pago_pendiente()

        # Act
        pago.marcar_fallido(referencia_externa="ext-1")

        # Assert
        assert pago.estado == EstadoPago.FALLIDO
        assert pago.referencia_externa == "ext-1"
        assert pago.fecha_pago is None

    def test_marcar_completado_raises_when_already_completado(self) -> None:
        # Arrange
        pago = _pago_pendiente()
        pago.marcar_completado(referencia_externa="ext-1")

        # Act / Assert
        with pytest.raises(PagoYaCompletado):
            pago.marcar_completado(referencia_externa="ext-2")

    def test_marcar_fallido_raises_when_already_completado(self) -> None:
        # Arrange
        pago = _pago_pendiente()
        pago.marcar_completado(referencia_externa="ext-1")

        # Act / Assert
        with pytest.raises(PagoYaCompletado):
            pago.marcar_fallido(referencia_externa="ext-2")

    def test_registrar_intento_sets_referencia_externa_without_changing_estado(self) -> None:
        # Arrange
        pago = _pago_pendiente()

        # Act
        pago.registrar_intento(referencia_externa="ext-1")

        # Assert
        assert pago.estado == EstadoPago.PENDIENTE
        assert pago.referencia_externa == "ext-1"

    def test_registrar_intento_raises_when_already_completado(self) -> None:
        # Arrange
        pago = _pago_pendiente()
        pago.marcar_completado(referencia_externa="ext-1")

        # Act / Assert
        with pytest.raises(PagoYaCompletado):
            pago.registrar_intento(referencia_externa="ext-2")

    def test_marcar_fallido_can_be_retried_towards_completado(self) -> None:
        """A `fallido` pago is not a final state — spec.md only forbids
        reiniciar un pago ya `completado`; the inquilino may retry a
        `fallido` one manually (design.md's non-goal on automatic
        retries only rules out *automatic* retries, not a subsequent
        manual `iniciar_pago` call succeeding)."""
        # Arrange
        pago = _pago_pendiente()
        pago.marcar_fallido(referencia_externa="ext-1")

        # Act
        pago.marcar_completado(referencia_externa="ext-2")

        # Assert
        assert pago.estado == EstadoPago.COMPLETADO
        assert pago.fecha_pago is not None
