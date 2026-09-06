"""Unit tests for `FakeAdapter`
(`pagos/infrastructure/adapters/fake_adapter.py`).

Covers task 2.1 of `openspec/changes/pago-mensual-renta/tasks.md`: per
design.md's "Estrategia de testing", this adapter always returns a
`completado` resultado with a deterministic `referencia_externa` (Fake:
completa inmediato) so tests exercising the happy path never need to mock
a variable pasarela response.

TDD Red phase: `pagos/infrastructure/adapters/fake_adapter.py` does not
exist yet, so this test is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 2.2).
"""

import uuid

from pagos.domain.ports import ResultadoCobro, SplitPago
from pagos.infrastructure.adapters.fake_adapter import FakeAdapter


def _split(**overrides: object) -> SplitPago:
    kwargs: dict[str, object] = {
        "monto_total": 1_500_000.0,
        "monto_prima_retenida": 50_000.0,
        "propietario_id": uuid.uuid4(),
    }
    kwargs.update(overrides)
    return SplitPago(**kwargs)  # type: ignore[arg-type]


class TestFakeAdapter:
    async def test_iniciar_cobro_returns_completado_with_referencia_externa(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado = await adapter.iniciar_cobro(_split())

        # Assert
        assert isinstance(resultado, ResultadoCobro)
        assert resultado.estado == "completado"
        assert resultado.referencia_externa

    async def test_iniciar_cobro_returns_deterministic_result_for_same_split(self) -> None:
        # Arrange
        adapter = FakeAdapter()
        propietario_id = uuid.uuid4()

        # Act
        primero = await adapter.iniciar_cobro(
            _split(monto_total=1_000_000.0, propietario_id=propietario_id)
        )
        segundo = await adapter.iniciar_cobro(
            _split(monto_total=1_000_000.0, propietario_id=propietario_id)
        )

        # Assert
        assert primero.referencia_externa == segundo.referencia_externa

    async def test_iniciar_cobro_returns_different_referencia_for_different_split(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado_a = await adapter.iniciar_cobro(_split(monto_total=1_000_000.0))
        resultado_b = await adapter.iniciar_cobro(_split(monto_total=2_000_000.0))

        # Assert
        assert resultado_a.referencia_externa != resultado_b.referencia_externa
