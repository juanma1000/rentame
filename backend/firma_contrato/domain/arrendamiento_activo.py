"""`ArrendamientoActivo` aggregate.

Business rules come from
`openspec/changes/firma-electronica-contrato-arrendamiento/specs/firma-contrato/spec.md`
(Requirement: "Contrato firmado crea un arrendamiento activo") and task
1.3-1.4 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`.

Same principle that led to modeling `PolizaArrendamiento` as its own
aggregate (design.md decisión 3): "documento firmado" (`Contrato`) and
"relación de arrendamiento en curso" (`ArrendamientoActivo`) are distinct
concepts with distinct lifecycles. Future capabilities (HU-006, pago
mensual) consult this aggregate, never `Contrato` directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum

from firma_contrato.domain.contrato import Contrato, EstadoContrato
from firma_contrato.domain.exceptions import ArrendamientoRequiereContratoFirmado


class EstadoArrendamientoActivo(str, Enum):
    ACTIVO = "activo"


@dataclass
class ArrendamientoActivo:
    """The active arrendamiento relationship produced by a `Contrato`
    reaching estado `firmado`.

    Instances must be built through `ArrendamientoActivo.crear`. `id` is
    `None` until a repository assigns one on insert — same pattern as
    `Contrato`/`PolizaArrendamiento`.
    """

    usuario_id: uuid.UUID
    poliza_id: uuid.UUID
    contrato_id: uuid.UUID
    inmueble_id: uuid.UUID
    estado: EstadoArrendamientoActivo
    fecha_inicio: date
    id: uuid.UUID | None = None

    @classmethod
    def crear(cls, *, contrato: Contrato) -> ArrendamientoActivo:
        """Build an `ArrendamientoActivo` out of a `Contrato`.

        Raises `ArrendamientoRequiereContratoFirmado` when `contrato.estado`
        is not `EstadoContrato.FIRMADO` — spec.md: "El sistema SHALL crear
        un ArrendamientoActivo únicamente cuando un Contrato pasa a estado
        firmado".
        """
        if contrato.estado != EstadoContrato.FIRMADO:
            raise ArrendamientoRequiereContratoFirmado(
                f"El contrato {contrato.id} no está firmado (estado actual: "
                f"{contrato.estado.value}); no se puede crear un ArrendamientoActivo"
            )
        if contrato.id is None:
            raise ArrendamientoRequiereContratoFirmado(
                "El contrato firmado debe tener un id asignado antes de crear un "
                "ArrendamientoActivo"
            )
        return cls(
            usuario_id=contrato.usuario_id,
            poliza_id=contrato.poliza_id,
            contrato_id=contrato.id,
            inmueble_id=contrato.inmueble_id,
            estado=EstadoArrendamientoActivo.ACTIVO,
            fecha_inicio=date.today(),
        )
