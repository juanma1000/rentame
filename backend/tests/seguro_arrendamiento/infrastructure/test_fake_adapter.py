"""Unit tests for `FakeAdapter`
(`seguro_arrendamiento/infrastructure/adapters/fake_adapter.py`).

Covers task 2.1 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`: per design.md's
"Estrategia de testing", this adapter always approves and returns a
deterministic `prima_mensual`/`referencia_externa`, so tests exercising the
happy path never need to mock a variable proveedor response.

TDD Red phase: `seguro_arrendamiento/infrastructure/adapters/fake_adapter.py`
does not exist yet, so this test is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 2.2).
"""

from seguro_arrendamiento.domain.ports import ResultadoPoliza
from seguro_arrendamiento.infrastructure.adapters.fake_adapter import FakeAdapter


class TestFakeAdapter:
    async def test_contratar_always_aprueba(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado = await adapter.contratar(cedula="1002003004", documentos=[b"doc1", b"doc2"])

        # Assert
        assert isinstance(resultado, ResultadoPoliza)
        assert resultado.aprobada is True
        assert resultado.referencia_externa
        assert resultado.prima_mensual is not None and resultado.prima_mensual > 0
        assert resultado.vigencia_desde is not None
        assert resultado.vigencia_hasta is not None
        assert resultado.vigencia_hasta > resultado.vigencia_desde

    async def test_contratar_returns_deterministic_result_for_same_cedula(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        primero = await adapter.contratar(cedula="1002003004", documentos=[b"a"])
        segundo = await adapter.contratar(cedula="1002003004", documentos=[b"b", b"c"])

        # Assert
        assert primero.referencia_externa == segundo.referencia_externa
        assert primero.prima_mensual == segundo.prima_mensual

    async def test_contratar_returns_different_referencia_externa_for_different_cedula(
        self,
    ) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado_a = await adapter.contratar(cedula="1002003004", documentos=[b"doc"])
        resultado_b = await adapter.contratar(cedula="9998887776", documentos=[b"doc"])

        # Assert
        assert resultado_a.referencia_externa != resultado_b.referencia_externa
