"""`generar_contrato` use case.

Orchestrates the "Generación de contrato requiere póliza aprobada" and "El
contenido legal del contrato lo genera Rentame" requirements of
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(tasks 3.1-3.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).

This module only orchestrates: it checks for an approved póliza up front
(cheap, avoids generating a document or calling the proveedor when the
gate fails), generates the legal document via
`template_contrato.generar_documento_contrato`, then delegates to
`Contrato` for every state transition — same pattern as
`seguro_arrendamiento.application.contratar_seguro_arrendamiento`.

`inmueble_id` travels on the command (not read from `PolizaArrendamiento`,
which has no such field — it only tracks `usuario_id`/prima/vigencia) so
`ArrendamientoActivo.crear` (invoked later, from the webhook use case) can
link the eventual arrendamiento to a specific inmueble, per
`docs/architecture/architecture.md`'s `INMUEBLE ||--o{ ARRENDAMIENTO_ACTIVO`
relationship.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from firma_contrato.application.template_contrato import generar_documento_contrato
from firma_contrato.domain.contrato import Contrato
from firma_contrato.domain.exceptions import PolizaNoAprobada
from firma_contrato.domain.ports import (
    ContratoRepositoryPort,
    PolizaArrendamientoPort,
    ProveedorFirmaElectronicaPort,
)


@dataclass
class GenerarContratoCommand:
    usuario_id: uuid.UUID
    inmueble_id: uuid.UUID
    nombre_inquilino: str
    nombre_propietario: str
    direccion_inmueble: str
    canon_mensual: float
    duracion_meses: int


async def generar_contrato(
    command: GenerarContratoCommand,
    *,
    contrato_repository: ContratoRepositoryPort,
    poliza_arrendamiento: PolizaArrendamientoPort,
    proveedor: ProveedorFirmaElectronicaPort,
) -> Contrato:
    """Run a generación de contrato de arrendamiento attempt for
    `command.usuario_id`.

    Raises `PolizaNoAprobada` when the account has no `PolizaArrendamiento`
    in estado `aprobada` — no `Contrato` is created and neither
    `proveedor.enviar_a_firma` nor `contrato_repository.guardar` is ever
    called (spec.md: "el sistema rechaza el intento sin generar ningún
    documento ni llamar al proveedor de firma").

    Otherwise generates the contrato's legal document from Rentame's own
    template, builds a `Contrato` in estado `borrador`, sends it to
    `proveedor.enviar_a_firma`, transitions it to `enviado_a_firma`, and
    persists it.
    """
    poliza_id = await poliza_arrendamiento.obtener_poliza_aprobada(command.usuario_id)
    if poliza_id is None:
        raise PolizaNoAprobada(
            f"La cuenta {command.usuario_id} no tiene una PolizaArrendamiento aprobada"
        )

    documento = generar_documento_contrato(
        nombre_inquilino=command.nombre_inquilino,
        nombre_propietario=command.nombre_propietario,
        direccion_inmueble=command.direccion_inmueble,
        canon_mensual=command.canon_mensual,
        duracion_meses=command.duracion_meses,
    )

    contrato = Contrato.generar(
        usuario_id=command.usuario_id,
        poliza_id=poliza_id,
        inmueble_id=command.inmueble_id,
        documento_referencia=documento,
    )

    resultado = await proveedor.enviar_a_firma(documento=documento)
    contrato.enviar_a_firma(referencia_externa=resultado.referencia_externa)

    return await contrato_repository.guardar(contrato)
