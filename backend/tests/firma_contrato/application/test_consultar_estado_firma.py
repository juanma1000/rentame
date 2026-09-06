"""Unit tests for the `consultar_estado_firma` use case
(`firma_contrato/application/consultar_estado_firma.py`).

Covers task 3.1 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`, the "Consulta de
estado del contrato y arrendamiento activo" requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/firma-contrato/spec.md`.

TDD Red phase: `firma_contrato/application/consultar_estado_firma.py` does
not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 3.2). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `consultar_estado_firma(usuario_id, *, contrato_repository,
  arrendamiento_repository) -> EstadoFirmaResult`: an async function that:
  1. Returns `estado="no_iniciado"`, `arrendamiento_activo_id=None` (a
     synthetic value, not part of `EstadoContrato`) when
     `contrato_repository.listar_por_usuario` returns an empty list — no
     proveedor externo call is ever made from this use case.
  2. Otherwise returns the `estado` of the most recent `Contrato` (highest
     `fecha`) belonging to that usuario, and — only when that contrato is
     `firmado` — the `id` of its associated `ArrendamientoActivo`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from firma_contrato.application.consultar_estado_firma import (
    ESTADO_NO_INICIADO,
    consultar_estado_firma,
)
from firma_contrato.domain.arrendamiento_activo import ArrendamientoActivo
from firma_contrato.domain.contrato import Contrato, EstadoContrato
from tests.firma_contrato.application.conftest import (
    FakeArrendamientoActivoRepository,
    FakeContratoRepository,
)


class TestConsultarEstadoFirmaSinContrato:
    async def test_should_return_no_iniciado_when_no_contrato_exists(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Act
        resultado = await consultar_estado_firma(
            uuid.uuid4(),
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO == "no_iniciado"
        assert resultado.arrendamiento_activo_id is None


class TestConsultarEstadoFirmaConContratoFirmado:
    async def test_should_return_firmado_with_arrendamiento_activo_id(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        contrato = Contrato.generar(
            usuario_id=usuario_id,
            poliza_id=uuid.uuid4(),
            inmueble_id=uuid.uuid4(),
            documento_referencia="doc-ref",
        )
        contrato.enviar_a_firma(referencia_externa="viafirma-1")
        contrato.marcar_firmado()
        contrato = await fake_contrato_repository.guardar(contrato)

        arrendamiento = ArrendamientoActivo.crear(contrato=contrato)
        arrendamiento = await fake_arrendamiento_repository.guardar(arrendamiento)

        # Act
        resultado = await consultar_estado_firma(
            usuario_id,
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert resultado.estado == "firmado"
        assert resultado.arrendamiento_activo_id == arrendamiento.id

    async def test_should_return_estado_of_the_most_recent_contrato_without_arrendamiento_id(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        antiguo = Contrato.generar(
            usuario_id=usuario_id,
            poliza_id=uuid.uuid4(),
            inmueble_id=uuid.uuid4(),
            documento_referencia="doc-antiguo",
        )
        antiguo.fecha = datetime(2026, 1, 1, tzinfo=UTC)
        await fake_contrato_repository.guardar(antiguo)

        reciente = Contrato.generar(
            usuario_id=usuario_id,
            poliza_id=uuid.uuid4(),
            inmueble_id=uuid.uuid4(),
            documento_referencia="doc-reciente",
        )
        reciente.enviar_a_firma(referencia_externa="viafirma-2")
        reciente.fecha = datetime(2026, 2, 1, tzinfo=UTC)
        await fake_contrato_repository.guardar(reciente)

        # Act
        resultado = await consultar_estado_firma(
            usuario_id,
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert resultado.estado == "enviado_a_firma"
        assert resultado.arrendamiento_activo_id is None

    async def test_should_not_return_another_usuarios_contrato(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_arrendamiento_repository: FakeArrendamientoActivoRepository,
    ) -> None:
        # Arrange
        otro_usuario = uuid.uuid4()
        await fake_contrato_repository.guardar(
            Contrato.generar(
                usuario_id=otro_usuario,
                poliza_id=uuid.uuid4(),
                inmueble_id=uuid.uuid4(),
                documento_referencia="doc-otro",
            )
        )

        # Act
        resultado = await consultar_estado_firma(
            uuid.uuid4(),
            contrato_repository=fake_contrato_repository,
            arrendamiento_repository=fake_arrendamiento_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO
        assert resultado.arrendamiento_activo_id is None
