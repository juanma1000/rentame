"""`SolicitudIngreso` entity and its lifecycle state machine.

Business rules and states come from
`openspec/changes/hu-007/specs/agencias/spec.md` (Requirement: "Ingreso a una
agencia existente requiere aprobación", tasks 1.8-1.9 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from shared.domain.exceptions import DomainValidationError


class EstadoSolicitudIngreso(StrEnum):
    """Lifecycle states of a `SolicitudIngreso`.

    - `PENDIENTE`: created by the agente requesting to join an agencia; the
      only state assigned at creation time.
    - `APROBADA`: accepted; terminal state.
    """

    PENDIENTE = "pendiente"
    APROBADA = "aprobada"


@dataclass
class SolicitudIngreso:
    """A request from an agente to join an existing `Agencia`.

    Instances must be built through `SolicitudIngreso.crear`, which always
    starts the entity in `EstadoSolicitudIngreso.PENDIENTE`.

    `id` is `None` until a repository assigns one on insert — same pattern as
    `Inmueble.crear` in `inmuebles/domain/inmueble.py`.
    """

    agencia_id: uuid.UUID
    agente_id: uuid.UUID
    estado: EstadoSolicitudIngreso
    id: uuid.UUID | None = None

    @classmethod
    def crear(cls, *, agencia_id: uuid.UUID, agente_id: uuid.UUID) -> SolicitudIngreso:
        """Create a new solicitud in `EstadoSolicitudIngreso.PENDIENTE`."""
        return cls(
            agencia_id=agencia_id,
            agente_id=agente_id,
            estado=EstadoSolicitudIngreso.PENDIENTE,
        )

    def aprobar(self) -> None:
        """Transition `PENDIENTE -> APROBADA`.

        Raises `DomainValidationError` when called again from `APROBADA`,
        leaving `estado` unchanged. Whether the approver is a member of the
        agencia belongs to the `aprobar_ingreso` use case (task 3.6), not to
        this entity method.
        """
        if self.estado != EstadoSolicitudIngreso.PENDIENTE:
            raise DomainValidationError(
                f"cannot aprobar a solicitud in estado {self.estado}, expected "
                f"{EstadoSolicitudIngreso.PENDIENTE}"
            )
        self.estado = EstadoSolicitudIngreso.APROBADA
