"""Unit tests for the `iniciar_validacion_identidad` use case
(`identidad/application/iniciar_validacion_identidad.py`).

Covers tasks 3.1-3.2 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`, the
"Validación de identidad vía cédula colombiana", "Resultado de validación
contra proveedor externo" and "Una sola validación exitosa por cuenta"
requirements of
`openspec/changes/validacion-identidad-inquilino/specs/identidad/spec.md`.

TDD Red phase: `identidad/application/iniciar_validacion_identidad.py` does
not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 3.3). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `IniciarValidacionIdentidadCommand`: a plain dataclass with
  `usuario_id: UUID`, `cedula: str`, `imagen_frente: bytes`,
  `imagen_dorso: bytes`.
- `iniciar_validacion_identidad(command, *, validacion_repository,
  usuario_repository, proveedor) -> ValidacionIdentidad`: an async function
  that:
  1. Raises `IdentidadYaVerificada` when
     `usuario_repository.esta_verificado(command.usuario_id)` is `True` —
     without ever calling `proveedor.validar(...)`.
  2. Otherwise calls `proveedor.validar(...)`, builds a `ValidacionIdentidad`
     reflecting the result, persists it via
     `validacion_repository.guardar`, and — only when the result is
     approved — marks the account verified via
     `usuario_repository.marcar_verificado`.
"""

import uuid

import pytest

from identidad.application.iniciar_validacion_identidad import (
    IniciarValidacionIdentidadCommand,
    iniciar_validacion_identidad,
)
from identidad.domain.exceptions import IdentidadYaVerificada
from identidad.domain.ports import ResultadoValidacion
from identidad.domain.validacion_identidad import EstadoValidacion
from identidad.infrastructure.adapters.fake_adapter import FakeAdapter
from tests.identidad.application.conftest import (
    FakeUsuarioIdentidadRepository,
    FakeValidacionIdentidadRepository,
    StubProveedorValidacionIdentidad,
)


def _command(**overrides: object) -> IniciarValidacionIdentidadCommand:
    kwargs: dict[str, object] = {
        "usuario_id": uuid.uuid4(),
        "cedula": "1002003004",
        "imagen_frente": b"frente",
        "imagen_dorso": b"dorso",
    }
    kwargs.update(overrides)
    return IniciarValidacionIdentidadCommand(**kwargs)  # type: ignore[arg-type]


class TestIniciarValidacionIdentidadAprobada:
    async def test_should_mark_usuario_identidad_verificada_when_proveedor_aprueba(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
        fake_usuario_repository: FakeUsuarioIdentidadRepository,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_repository.seed(command.usuario_id, False)

        # Act
        validacion = await iniciar_validacion_identidad(
            command,
            validacion_repository=fake_validacion_repository,
            usuario_repository=fake_usuario_repository,
            proveedor=FakeAdapter(),
        )

        # Assert
        assert validacion.estado == EstadoValidacion.APROBADO
        assert validacion.id is not None
        assert fake_validacion_repository.guardar_calls == [validacion]
        assert await fake_usuario_repository.esta_verificado(command.usuario_id) is True
        assert fake_usuario_repository.marcar_verificado_calls == [command.usuario_id]


class TestIniciarValidacionIdentidadRechazada:
    async def test_should_not_mark_identidad_verificada_when_proveedor_rechaza(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
        fake_usuario_repository: FakeUsuarioIdentidadRepository,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_repository.seed(command.usuario_id, False)
        stub_proveedor = StubProveedorValidacionIdentidad(
            resultado=ResultadoValidacion(aprobado=False, referencia_externa="truora-rechazo-1")
        )

        # Act
        validacion = await iniciar_validacion_identidad(
            command,
            validacion_repository=fake_validacion_repository,
            usuario_repository=fake_usuario_repository,
            proveedor=stub_proveedor,
        )

        # Assert
        assert validacion.estado == EstadoValidacion.RECHAZADO
        assert validacion.referencia_externa == "truora-rechazo-1"
        assert fake_validacion_repository.guardar_calls == [validacion]
        assert await fake_usuario_repository.esta_verificado(command.usuario_id) is False
        assert fake_usuario_repository.marcar_verificado_calls == []


class TestIniciarValidacionIdentidadCuentaYaVerificada:
    async def test_should_raise_identidad_ya_verificada_without_calling_proveedor(
        self,
        fake_validacion_repository: FakeValidacionIdentidadRepository,
        fake_usuario_repository: FakeUsuarioIdentidadRepository,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_repository.seed(command.usuario_id, True)
        stub_proveedor = StubProveedorValidacionIdentidad(
            resultado=ResultadoValidacion(aprobado=True, referencia_externa="no-deberia-llamarse")
        )

        # Act / Assert
        with pytest.raises(IdentidadYaVerificada):
            await iniciar_validacion_identidad(
                command,
                validacion_repository=fake_validacion_repository,
                usuario_repository=fake_usuario_repository,
                proveedor=stub_proveedor,
            )

        assert stub_proveedor.calls == []
        assert fake_validacion_repository.guardar_calls == []
