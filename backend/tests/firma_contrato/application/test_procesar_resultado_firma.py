"""Unit tests for the `procesar_resultado_firma` use case
(`firma_contrato/application/procesar_resultado_firma.py`), invoked by the
webhook endpoint.

Covers task 4.1 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`, the
"Contrato firmado crea un arrendamiento activo" and "Póliza queda huérfana
ante rechazo o expiración del contrato" requirements of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`.

TDD Red phase:
`firma_contrato/application/procesar_resultado_firma.py` does not exist
yet, so every test here is expected to fail with `ModuleNotFoundError`
until `backend-expert` implements it (task 4.2). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `procesar_resultado_firma(resultado: ResultadoFirmaWebhook, *,
  contrato_repository, arrendamiento_repository) -> Contrato`: an async
  function that:
  1. Locates the `Contrato` via
     `contrato_repository.obtener_por_referencia_externa`. Raises
     `ContratoNoEncontrado` when none matches.
  2. Raises `ContratoNoEnviadoAFirma` when the located contrato is not in
     estado `enviado_a_firma` (duplicate/out-of-order webhook).
  3. `resultado.estado == "firmado"`: marks the contrato `firmado`,
     persists it, then creates an `ArrendamientoActivo` from it and
     persists that too.
  4. `resultado.estado in ("rechazado", "expirado")`: marks the contrato
     with that estado and persists it — no `ArrendamientoActivo` is ever
     created, and no other aggregate (in particular, no
     `PolizaArrendamiento`) is touched.
"""

import uuid

import pytest

from firma_contrato.application.procesar_resultado_firma import (
    ContratoNoEncontrado,
    procesar_resultado_firma,
)
from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.domain.exceptions import ContratoNoEnviadoAFirma
from firma_contrato.domain.ports import ResultadoFirmaWebhook
from tests.firma_contrato.application.conftest import (
    FakeArrendamientoActivoRepository,
    FakeContratoRepository,
)


def _contrato_enviado_a_firma(referencia_externa: str = "ext-1") -> Contrato:
    contrato = Contrato.generar(
        usuario_id=uuid.uuid4(),
        poliza_id=uuid.uuid4(),
        inmueble_id=uuid.uuid4(),
        documento_referencia="contrato-texto-generado",
    )
    contrato.enviar_a_firma(referencia_externa=referencia_externa)
    return contrato


class TestProcesarResultadoFirmaFirmado:
    async def test_should_mark_contrato_firmado_and_create_arrendamiento_activo(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        contrato = await fake_contrato_repository.guardar(_contrato_enviado_a_firma())
        resultado = ResultadoFirmaWebhook(referencia_externa="ext-1", estado="firmado")

        # Act
        actualizado = await procesar_resultado_firma(
            resultado,
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert actualizado.estado == EstadoContrato.FIRMADO
        assert fake_contrato_repository.actualizar_calls == [actualizado]
        assert len(fake_arrendamiento_repository.guardar_calls) == 1
        arrendamiento = fake_arrendamiento_repository.guardar_calls[0]
        assert arrendamiento.contrato_id == contrato.id
        assert arrendamiento.usuario_id == contrato.usuario_id
        assert arrendamiento.poliza_id == contrato.poliza_id


class TestProcesarResultadoFirmaRechazadoExpirado:
    async def test_rechazado_marks_contrato_without_creating_arrendamiento(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        await fake_contrato_repository.guardar(_contrato_enviado_a_firma())
        resultado = ResultadoFirmaWebhook(referencia_externa="ext-1", estado="rechazado")

        # Act
        actualizado = await procesar_resultado_firma(
            resultado,
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert actualizado.estado == EstadoContrato.RECHAZADO
        assert fake_arrendamiento_repository.guardar_calls == []

    async def test_expirado_marks_contrato_without_creating_arrendamiento(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        await fake_contrato_repository.guardar(_contrato_enviado_a_firma())
        resultado = ResultadoFirmaWebhook(referencia_externa="ext-1", estado="expirado")

        # Act
        actualizado = await procesar_resultado_firma(
            resultado,
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert actualizado.estado == EstadoContrato.EXPIRADO
        assert fake_arrendamiento_repository.guardar_calls == []


class TestProcesarResultadoFirmaErrores:
    async def test_raises_contrato_no_encontrado_when_referencia_does_not_match(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        resultado = ResultadoFirmaWebhook(referencia_externa="no-existe", estado="firmado")

        # Act / Assert
        with pytest.raises(ContratoNoEncontrado):
            await procesar_resultado_firma(
                resultado,
                contrato_repository=fake_contrato_repository,
                arrendamiento_repository=fake_arrendamiento_repository,
            )

    async def test_raises_contrato_no_enviado_a_firma_when_already_firmado(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        contrato = _contrato_enviado_a_firma()
        contrato.marcar_firmado()
        await fake_contrato_repository.guardar(contrato)
        resultado = ResultadoFirmaWebhook(referencia_externa="ext-1", estado="firmado")

        # Act / Assert
        with pytest.raises(ContratoNoEnviadoAFirma):
            await procesar_resultado_firma(
                resultado,
                contrato_repository=fake_contrato_repository,
                arrendamiento_repository=fake_arrendamiento_repository,
            )
