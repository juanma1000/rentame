"""Unit tests for the `ValidacionIdentidad` aggregate
(`identidad/domain/validacion_identidad.py`).

Pure domain tests: no database, no HTTP. They express the "Validación de
identidad vía cédula colombiana" and "Una sola validación exitosa por
cuenta" requirements of
`openspec/changes/validacion-identidad-inquilino/specs/identidad/spec.md`
(task 1.1 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`).

TDD Red phase: `identidad/domain/validacion_identidad.py` does not exist
yet, so this test is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 1.2). This file fixes, by
construction, the contract the implementation must satisfy:

- `EstadoValidacion` enum: `PENDIENTE`, `APROBADO`, `RECHAZADO`.
- `ValidacionIdentidad.iniciar(*, usuario_id, cedula, validaciones_existentes)`
  is a factory classmethod. It raises
  `identidad.domain.exceptions.IdentidadYaVerificada` when
  `validaciones_existentes` already contains one in `EstadoValidacion.APROBADO`
  — the "una sola validación aprobada por cuenta" invariant, enforced without
  touching any repository. Otherwise it returns a new `ValidacionIdentidad`
  in `EstadoValidacion.PENDIENTE`, with `id is None` (assigned by the
  repository on insert, same pattern as `Agencia.crear`).
- `.aprobar(referencia_externa=...)` transitions to `APROBADO` and stores the
  external reference.
- `.rechazar(referencia_externa=...)` transitions to `RECHAZADO` and stores
  the external reference (still auditable, per design.md's testing strategy).
"""

import uuid

import pytest

from identidad.domain.exceptions import IdentidadYaVerificada
from identidad.domain.validacion_identidad import EstadoValidacion, ValidacionIdentidad


class TestValidacionIdentidadIniciar:
    def test_should_create_pendiente_validacion_when_no_previous_validaciones(self) -> None:
        # Arrange
        usuario_id = uuid.uuid4()

        # Act
        validacion = ValidacionIdentidad.iniciar(
            usuario_id=usuario_id, cedula="1002003004", validaciones_existentes=[]
        )

        # Assert
        assert validacion.usuario_id == usuario_id
        assert validacion.cedula == "1002003004"
        assert validacion.estado == EstadoValidacion.PENDIENTE
        assert validacion.id is None
        assert validacion.referencia_externa is None

    def test_should_create_pendiente_validacion_when_previous_validaciones_were_rechazadas(
        self,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        rechazada = ValidacionIdentidad.iniciar(
            usuario_id=usuario_id, cedula="1002003004", validaciones_existentes=[]
        )
        rechazada.rechazar(referencia_externa="ext-1")

        # Act
        validacion = ValidacionIdentidad.iniciar(
            usuario_id=usuario_id,
            cedula="1002003004",
            validaciones_existentes=[rechazada],
        )

        # Assert
        assert validacion.estado == EstadoValidacion.PENDIENTE

    def test_should_raise_identidad_ya_verificada_when_an_aprobada_validacion_already_exists(
        self,
    ) -> None:
        # Arrange
        usuario_id = uuid.uuid4()
        aprobada = ValidacionIdentidad.iniciar(
            usuario_id=usuario_id, cedula="1002003004", validaciones_existentes=[]
        )
        aprobada.aprobar(referencia_externa="ext-1")

        # Act / Assert
        with pytest.raises(IdentidadYaVerificada):
            ValidacionIdentidad.iniciar(
                usuario_id=usuario_id,
                cedula="1002003004",
                validaciones_existentes=[aprobada],
            )


class TestValidacionIdentidadTransiciones:
    def test_aprobar_sets_estado_aprobado_and_referencia_externa(self) -> None:
        # Arrange
        validacion = ValidacionIdentidad.iniciar(
            usuario_id=uuid.uuid4(), cedula="1002003004", validaciones_existentes=[]
        )

        # Act
        validacion.aprobar(referencia_externa="truora-ref-123")

        # Assert
        assert validacion.estado == EstadoValidacion.APROBADO
        assert validacion.referencia_externa == "truora-ref-123"

    def test_rechazar_sets_estado_rechazado_and_referencia_externa(self) -> None:
        # Arrange
        validacion = ValidacionIdentidad.iniciar(
            usuario_id=uuid.uuid4(), cedula="1002003004", validaciones_existentes=[]
        )

        # Act
        validacion.rechazar(referencia_externa="truora-ref-456")

        # Assert
        assert validacion.estado == EstadoValidacion.RECHAZADO
        assert validacion.referencia_externa == "truora-ref-456"
