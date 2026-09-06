"""Unit tests for the `generar_contrato` use case
(`firma_contrato/application/generar_contrato.py`).

Covers tasks 3.1-3.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`, the
"Generación de contrato requiere póliza aprobada" and "El contenido legal
del contrato lo genera Rentame" requirements of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`.

TDD Red phase:
`firma_contrato/application/generar_contrato.py` does not exist yet, so
every test here is expected to fail with `ModuleNotFoundError` until
`backend-expert` implements it (task 3.2). This file fixes, by
construction, the contract `backend-expert` must satisfy:

- `GenerarContratoCommand`: a dataclass with `usuario_id: UUID`,
  `inmueble_id: UUID`, `nombre_inquilino: str`, `nombre_propietario: str`,
  `direccion_inmueble: str`, `canon_mensual: float`,
  `duracion_meses: int`.
- `generar_contrato(command, *, contrato_repository, poliza_arrendamiento,
  proveedor) -> Contrato`: an async function that:
  1. Raises `PolizaNoAprobada` when
     `poliza_arrendamiento.obtener_poliza_aprobada(command.usuario_id)` is
     `None` — without ever calling `proveedor.enviar_a_firma(...)` nor
     `contrato_repository.guardar(...)`.
  2. Otherwise generates the contrato's legal document via the project's
     own template (`generar_documento_contrato`), builds a `Contrato` in
     estado `borrador` referencing the found póliza, sends it to
     `proveedor.enviar_a_firma`, transitions it to `enviado_a_firma`, and
     persists it (`contrato_repository.guardar`).
"""

import uuid

import pytest

from firma_contrato.application.generar_contrato import (
    GenerarContratoCommand,
    generar_contrato,
)
from firma_contrato.domain.contrato import EstadoContrato
from firma_contrato.domain.exceptions import PolizaNoAprobada
from firma_contrato.domain.ports import ResultadoEnvioFirma
from firma_contrato.infrastructure.adapters.fake_adapter import FakeAdapter
from tests.firma_contrato.application.conftest import (
    FakeContratoRepository,
    FakePolizaArrendamiento,
    StubProveedorFirmaElectronica,
)


def _command(**overrides: object) -> GenerarContratoCommand:
    kwargs: dict[str, object] = {
        "usuario_id": uuid.uuid4(),
        "inmueble_id": uuid.uuid4(),
        "nombre_inquilino": "Juan Pérez",
        "nombre_propietario": "María Gómez",
        "direccion_inmueble": "Calle 10 # 20-30, Cali",
        "canon_mensual": 1500000.0,
        "duracion_meses": 12,
    }
    kwargs.update(overrides)
    return GenerarContratoCommand(**kwargs)  # type: ignore[arg-type]


class TestGenerarContratoSinPolizaAprobada:
    async def test_should_raise_poliza_no_aprobada_without_generating_document_or_calling_proveedor(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
    ) -> None:
        # Arrange
        command = _command()
        stub_proveedor = StubProveedorFirmaElectronica(
            resultado=ResultadoEnvioFirma(referencia_externa="no-deberia-llamarse")
        )

        # Act / Assert
        with pytest.raises(PolizaNoAprobada):
            await generar_contrato(
                command,
                contrato_repository=fake_contrato_repository,
                poliza_arrendamiento=fake_poliza_arrendamiento,
                proveedor=stub_proveedor,
            )

        assert stub_proveedor.calls == []
        assert fake_contrato_repository.guardar_calls == []


class TestGenerarContratoConPolizaAprobada:
    async def test_should_generate_contrato_and_send_to_firma(
        self,
        fake_contrato_repository: FakeContratoRepository,
        fake_poliza_arrendamiento: FakePolizaArrendamiento,
    ) -> None:
        # Arrange
        command = _command()
        poliza_id = uuid.uuid4()
        fake_poliza_arrendamiento.seed_aprobada(command.usuario_id, poliza_id)

        # Act
        contrato = await generar_contrato(
            command,
            contrato_repository=fake_contrato_repository,
            poliza_arrendamiento=fake_poliza_arrendamiento,
            proveedor=FakeAdapter(),
        )

        # Assert
        assert contrato.usuario_id == command.usuario_id
        assert contrato.poliza_id == poliza_id
        assert contrato.inmueble_id == command.inmueble_id
        assert contrato.estado == EstadoContrato.ENVIADO_A_FIRMA
        assert contrato.referencia_externa
        assert contrato.documento_referencia
        assert "Juan Pérez" in contrato.documento_referencia
        assert "María Gómez" in contrato.documento_referencia
        assert contrato.id is not None
        assert fake_contrato_repository.guardar_calls == [contrato]
