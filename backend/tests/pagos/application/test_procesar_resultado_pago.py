"""Unit tests for the `procesar_resultado_pago` use case
(`pagos/application/procesar_resultado_pago.py`), invoked by the
`POST /pagos/webhook` endpoint.

Covers task 5.1 of `openspec/changes/pago-mensual-renta/tasks.md`, the
"Resultado modelado como pago con estado propio" requirement of
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md`.

TDD Red phase: `pagos/application/procesar_resultado_pago.py` does not
exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 5.2).
This file fixes, by construction, the contract to satisfy:

- `procesar_resultado_pago(resultado: ResultadoWebhookPago, *,
  pago_repository) -> Pago`: an async function that:
  1. Locates the `Pago` via `pago_repository.obtener_por_referencia_externa`.
     Raises `PagoNoEncontrado` when none matches.
  2. `resultado.estado == "completado"`: marks the pago `completado` with
     `fecha_pago` set.
  3. `resultado.estado == "fallido"`: marks the pago `fallido`, with no
     `fecha_pago`.
"""

from datetime import date, timedelta

import pytest

from pagos.application.procesar_resultado_pago import procesar_resultado_pago
from pagos.domain.exceptions import PagoNoEncontrado
from pagos.domain.pago import EstadoPago, Pago
from pagos.domain.ports import ResultadoWebhookPago
from tests.pagos.application.conftest import FakePagoRepository


async def _pago_pendiente_guardado(
    fake_pago_repository: FakePagoRepository, referencia_externa: str = "ext-1"
) -> Pago:
    import uuid

    pago = Pago.crear(
        arrendamiento_activo_id=uuid.uuid4(),
        monto=1_500_000.0,
        fecha_limite=date.today() + timedelta(days=5),
    )
    pago = await fake_pago_repository.guardar(pago)
    pago.registrar_intento(referencia_externa=referencia_externa)
    return await fake_pago_repository.actualizar(pago)


class TestProcesarResultadoPagoCompletado:
    async def test_marks_pago_completado_with_fecha_pago(
        self, fake_pago_repository: FakePagoRepository
    ) -> None:
        # Arrange
        await _pago_pendiente_guardado(fake_pago_repository, referencia_externa="ext-1")
        resultado = ResultadoWebhookPago(referencia_externa="ext-1", estado="completado")

        # Act
        actualizado = await procesar_resultado_pago(
            resultado, pago_repository=fake_pago_repository
        )

        # Assert
        assert actualizado.estado == EstadoPago.COMPLETADO
        assert actualizado.fecha_pago is not None
        assert fake_pago_repository.actualizar_calls[-1] == actualizado


class TestProcesarResultadoPagoFallido:
    async def test_marks_pago_fallido_without_fecha_pago(
        self, fake_pago_repository: FakePagoRepository
    ) -> None:
        # Arrange
        await _pago_pendiente_guardado(fake_pago_repository, referencia_externa="ext-2")
        resultado = ResultadoWebhookPago(referencia_externa="ext-2", estado="fallido")

        # Act
        actualizado = await procesar_resultado_pago(
            resultado, pago_repository=fake_pago_repository
        )

        # Assert
        assert actualizado.estado == EstadoPago.FALLIDO
        assert actualizado.fecha_pago is None


class TestProcesarResultadoPagoErrores:
    async def test_raises_pago_no_encontrado_when_referencia_does_not_match(
        self, fake_pago_repository: FakePagoRepository
    ) -> None:
        # Arrange
        resultado = ResultadoWebhookPago(referencia_externa="no-existe", estado="completado")

        # Act / Assert
        with pytest.raises(PagoNoEncontrado):
            await procesar_resultado_pago(resultado, pago_repository=fake_pago_repository)
