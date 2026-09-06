"""Unit tests for the `contratar_seguro_arrendamiento` use case
(`seguro_arrendamiento/application/contratar_seguro_arrendamiento.py`).

Covers tasks 3.1-3.2 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`, the
"Contratación de seguro de arrendamiento requiere identidad verificada" and
"Resultado modelado como póliza con estado propio" requirements of
`openspec/changes/seguro-arrendamiento-inquilino/specs/seguro-arrendamiento/spec.md`.

TDD Red phase:
`seguro_arrendamiento/application/contratar_seguro_arrendamiento.py` does
not exist yet, so every test here is expected to fail with
`ModuleNotFoundError` until `backend-expert` implements it (task 3.3). This
file fixes, by construction, the contract `backend-expert` must satisfy:

- `ContratarSeguroArrendamientoCommand`: a plain dataclass with
  `usuario_id: UUID`, `cedula: str`, `documentos: list[bytes]`.
- `contratar_seguro_arrendamiento(command, *, poliza_repository,
  usuario_identidad, proveedor) -> PolizaArrendamiento`: an async function
  that:
  1. Raises `IdentidadNoVerificada` when
     `usuario_identidad.esta_verificado(command.usuario_id)` is `False` —
     without ever calling `proveedor.contratar(...)`.
  2. Otherwise calls `proveedor.contratar(...)`, builds a
     `PolizaArrendamiento` reflecting the result, and persists it via
     `poliza_repository.guardar` (`aprobada` when the proveedor approves,
     `rechazada` otherwise — either way persisted for audit).
"""

import uuid

import pytest

from seguro_arrendamiento.application.contratar_seguro_arrendamiento import (
    ContratarSeguroArrendamientoCommand,
    contratar_seguro_arrendamiento,
)
from seguro_arrendamiento.domain.exceptions import IdentidadNoVerificada
from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza
from seguro_arrendamiento.domain.ports import ResultadoPoliza
from seguro_arrendamiento.infrastructure.adapters.fake_adapter import FakeAdapter
from tests.seguro_arrendamiento.application.conftest import (
    FakePolizaArrendamientoRepository,
    FakeUsuarioIdentidad,
    StubProveedorSeguroArrendamiento,
)


def _command(**overrides: object) -> ContratarSeguroArrendamientoCommand:
    kwargs: dict[str, object] = {
        "usuario_id": uuid.uuid4(),
        "cedula": "1002003004",
        "documentos": [b"desprendible", b"certificado"],
    }
    kwargs.update(overrides)
    return ContratarSeguroArrendamientoCommand(**kwargs)  # type: ignore[arg-type]


class TestContratarSeguroArrendamientoAprobada:
    async def test_should_create_poliza_aprobada_when_identidad_verificada_and_proveedor_aprueba(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
        fake_usuario_identidad: FakeUsuarioIdentidad,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_identidad.seed(command.usuario_id, True)

        # Act
        poliza = await contratar_seguro_arrendamiento(
            command,
            poliza_repository=fake_poliza_repository,
            usuario_identidad=fake_usuario_identidad,
            proveedor=FakeAdapter(),
        )

        # Assert
        assert poliza.estado == EstadoPoliza.APROBADA
        assert poliza.id is not None
        assert poliza.prima_mensual is not None
        assert fake_poliza_repository.guardar_calls == [poliza]


class TestContratarSeguroArrendamientoRechazada:
    async def test_should_persist_poliza_rechazada_when_proveedor_rechaza(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
        fake_usuario_identidad: FakeUsuarioIdentidad,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_identidad.seed(command.usuario_id, True)
        stub_proveedor = StubProveedorSeguroArrendamiento(
            resultado=ResultadoPoliza(aprobada=False, referencia_externa="sura-rechazo-1")
        )

        # Act
        poliza = await contratar_seguro_arrendamiento(
            command,
            poliza_repository=fake_poliza_repository,
            usuario_identidad=fake_usuario_identidad,
            proveedor=stub_proveedor,
        )

        # Assert
        assert poliza.estado == EstadoPoliza.RECHAZADA
        assert poliza.referencia_externa == "sura-rechazo-1"
        assert fake_poliza_repository.guardar_calls == [poliza]


class TestContratarSeguroArrendamientoIdentidadNoVerificada:
    async def test_should_raise_identidad_no_verificada_without_calling_proveedor(
        self,
        fake_poliza_repository: FakePolizaArrendamientoRepository,
        fake_usuario_identidad: FakeUsuarioIdentidad,
    ) -> None:
        # Arrange
        command = _command()
        fake_usuario_identidad.seed(command.usuario_id, False)
        stub_proveedor = StubProveedorSeguroArrendamiento(
            resultado=ResultadoPoliza(aprobada=True, referencia_externa="no-deberia-llamarse")
        )

        # Act / Assert
        with pytest.raises(IdentidadNoVerificada):
            await contratar_seguro_arrendamiento(
                command,
                poliza_repository=fake_poliza_repository,
                usuario_identidad=fake_usuario_identidad,
                proveedor=stub_proveedor,
            )

        assert stub_proveedor.calls == []
        assert fake_poliza_repository.guardar_calls == []
