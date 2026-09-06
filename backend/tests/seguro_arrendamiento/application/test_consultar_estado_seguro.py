"""Unit tests for the `consultar_estado_seguro` use case
(`seguro_arrendamiento/application/consultar_estado_seguro.py`).

Covers task 2.1 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`, the "Consulta de
estado de la póliza de seguro de arrendamiento" requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/seguro-arrendamiento/spec.md`.

TDD Red phase: `seguro_arrendamiento/application/consultar_estado_seguro.py`
does not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 2.2). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `consultar_estado_seguro(usuario_id, *, poliza_repository) ->
  EstadoSeguroResult`: an async function that:
  1. Returns `estado="no_iniciado"`, `prima_mensual=None` (a synthetic
     value, not part of `EstadoPoliza`) when
     `poliza_repository.listar_por_usuario` returns an empty list — no
     proveedor externo call is ever made from this use case.
  2. Otherwise returns the `estado` and `prima_mensual` of the most recent
     `PolizaArrendamiento` (highest `fecha`) belonging to that usuario.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from seguro_arrendamiento.application.consultar_estado_seguro import (
    ESTADO_NO_INICIADO,
    consultar_estado_seguro,
)
from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza, PolizaArrendamiento
from tests.seguro_arrendamiento.application.conftest import FakePolizaArrendamientoRepository


class TestConsultarEstadoSeguroSinPoliza:
    async def test_should_return_no_iniciado_when_no_poliza_exists(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
    ) -> None:
        # Act
        resultado = await consultar_estado_seguro(
            uuid.uuid4(),
            poliza_repository=fake_poliza_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO == "no_iniciado"
        assert resultado.prima_mensual is None


class TestConsultarEstadoSeguroConPolizaAprobada:
    async def test_should_return_estado_and_prima_mensual_of_the_most_recent_poliza(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        pendiente = PolizaArrendamiento(
            usuario_id=usuario_id,
            estado=EstadoPoliza.PENDIENTE,
            fecha=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        aprobada = PolizaArrendamiento(
            usuario_id=usuario_id,
            estado=EstadoPoliza.APROBADA,
            fecha=datetime(2026, 2, 1, tzinfo=timezone.utc),
            prima_mensual=85000.0,
        )
        await fake_poliza_repository.guardar(pendiente)
        await fake_poliza_repository.guardar(aprobada)

        # Act
        resultado = await consultar_estado_seguro(
            usuario_id,
            poliza_repository=fake_poliza_repository,
        )

        # Assert
        assert resultado.estado == "aprobada"
        assert resultado.prima_mensual == 85000.0

    async def test_should_not_return_another_usuarios_poliza(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
    ) -> None:
        # Arrange
        otro_usuario = uuid.uuid4()
        await fake_poliza_repository.guardar(
            PolizaArrendamiento(
                usuario_id=otro_usuario,
                estado=EstadoPoliza.APROBADA,
                fecha=datetime.now(timezone.utc),
                prima_mensual=85000.0,
            )
        )

        # Act
        resultado = await consultar_estado_seguro(
            uuid.uuid4(),
            poliza_repository=fake_poliza_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO
        assert resultado.prima_mensual is None
