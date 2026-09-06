"""Unit tests for `FakeAdapter`
(`identidad/infrastructure/adapters/fake_adapter.py`).

Covers task 2.1 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`: per design.md
decisión 4, this adapter always approves and returns a deterministic
`referencia_externa`, so tests exercising the happy path never need to mock
a variable proveedor response.

TDD Red phase: `identidad/infrastructure/adapters/fake_adapter.py` does not
exist yet, so this test is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 2.2).
"""

from identidad.domain.ports import ResultadoValidacion
from identidad.infrastructure.adapters.fake_adapter import FakeAdapter


class TestFakeAdapter:
    async def test_validar_always_approves(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado = await adapter.validar(
            cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )

        # Assert
        assert isinstance(resultado, ResultadoValidacion)
        assert resultado.aprobado is True
        assert resultado.referencia_externa

    async def test_validar_returns_deterministic_referencia_externa_for_same_cedula(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        primero = await adapter.validar(
            cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )
        segundo = await adapter.validar(
            cedula="1002003004", imagen_frente=b"otra-frente", imagen_dorso=b"otra-dorso"
        )

        # Assert
        assert primero.referencia_externa == segundo.referencia_externa

    async def test_validar_returns_different_referencia_externa_for_different_cedula(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado_a = await adapter.validar(
            cedula="1002003004", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )
        resultado_b = await adapter.validar(
            cedula="9998887776", imagen_frente=b"frente", imagen_dorso=b"dorso"
        )

        # Assert
        assert resultado_a.referencia_externa != resultado_b.referencia_externa
