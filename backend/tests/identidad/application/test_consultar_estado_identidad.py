"""Unit tests for the `consultar_estado_identidad` use case
(`identidad/application/consultar_estado_identidad.py`).

Covers task 1.1 of
`openspec/changes/frontend-flujo-arrendamiento/tasks.md`, the "Consulta de
estado de validación de identidad" requirement of
`openspec/changes/frontend-flujo-arrendamiento/specs/identidad/spec.md`.

TDD Red phase: `identidad/application/consultar_estado_identidad.py` does
not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 1.2). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `consultar_estado_identidad(usuario_id, *, validacion_repository) ->
  EstadoIdentidadResult`: an async function that:
  1. Returns `estado="no_iniciado"` (a synthetic value, not part of
     `EstadoValidacion`) when `validacion_repository.listar_por_usuario`
     returns an empty list — no proveedor externo call is ever made from
     this use case (it is purely a read over already-persisted data).
  2. Otherwise returns the `estado` of the most recent `ValidacionIdentidad`
     (highest `fecha`) belonging to that usuario.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from identidad.application.consultar_estado_identidad import (
    ESTADO_NO_INICIADO,
    consultar_estado_identidad,
)
from identidad.domain.validacion_identidad import EstadoValidacion, ValidacionIdentidad
from tests.identidad.application.conftest import FakeValidacionIdentidadRepository


class TestConsultarEstadoIdentidadSinValidaciones:
    async def test_should_return_no_iniciado_when_no_validacion_exists(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
    ) -> None:
        # Act
        resultado = await consultar_estado_identidad(
            uuid.uuid4(),
            validacion_repository=fake_validacion_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO == "no_iniciado"


class TestConsultarEstadoIdentidadConValidacion:
    async def test_should_return_estado_of_the_most_recent_validacion(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        rechazada = ValidacionIdentidad(
            usuario_id=usuario_id,
            cedula="1002003004",
            estado=EstadoValidacion.RECHAZADO,
            fecha=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        aprobada = ValidacionIdentidad(
            usuario_id=usuario_id,
            cedula="1002003004",
            estado=EstadoValidacion.APROBADO,
            fecha=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        await fake_validacion_repository.guardar(rechazada)
        await fake_validacion_repository.guardar(aprobada)

        # Act
        resultado = await consultar_estado_identidad(
            usuario_id,
            validacion_repository=fake_validacion_repository,
        )

        # Assert
        assert resultado.estado == "aprobado"

    async def test_should_not_return_another_usuarios_validacion(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
    ) -> None:
        # Arrange
        otro_usuario = uuid.uuid4()
        await fake_validacion_repository.guardar(
            ValidacionIdentidad(
                usuario_id=otro_usuario,
                cedula="1002003004",
                estado=EstadoValidacion.APROBADO,
                fecha=datetime.now(timezone.utc),
            )
        )

        # Act
        resultado = await consultar_estado_identidad(
            uuid.uuid4(),
            validacion_repository=fake_validacion_repository,
        )

        # Assert
        assert resultado.estado == ESTADO_NO_INICIADO
