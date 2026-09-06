"""Unit tests for `FakeAdapter`
(`firma_contrato/infrastructure/adapters/fake_adapter.py`).

Covers task 2.1 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`: per
design.md's "Estrategia de testing", this adapter always returns a
deterministic `referencia_externa` (Fake: firma inmediato) so tests
exercising the happy path never need to mock a variable proveedor
response.

TDD Red phase: `firma_contrato/infrastructure/adapters/fake_adapter.py`
does not exist yet, so this test is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 2.2).
"""

from firma_contrato.domain.ports import ResultadoEnvioFirma
from firma_contrato.infrastructure.adapters.fake_adapter import FakeAdapter


class TestFakeAdapter:
    async def test_enviar_a_firma_returns_referencia_externa(self) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado = await adapter.enviar_a_firma(documento="contrato-texto-generado")

        # Assert
        assert isinstance(resultado, ResultadoEnvioFirma)
        assert resultado.referencia_externa

    async def test_enviar_a_firma_returns_deterministic_result_for_same_documento(
        self,
    ) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        primero = await adapter.enviar_a_firma(documento="contrato-texto-generado")
        segundo = await adapter.enviar_a_firma(documento="contrato-texto-generado")

        # Assert
        assert primero.referencia_externa == segundo.referencia_externa

    async def test_enviar_a_firma_returns_different_referencia_for_different_documento(
        self,
    ) -> None:
        # Arrange
        adapter = FakeAdapter()

        # Act
        resultado_a = await adapter.enviar_a_firma(documento="documento-a")
        resultado_b = await adapter.enviar_a_firma(documento="documento-b")

        # Assert
        assert resultado_a.referencia_externa != resultado_b.referencia_externa
