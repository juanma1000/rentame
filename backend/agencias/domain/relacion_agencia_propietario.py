"""`RelacionAgenciaPropietario` entity and its lifecycle state machine.

Business rules and states come from
`openspec/changes/hu-007/specs/agencias/spec.md` (Requirements: "Relación
agencia-propietario iniciada por el propietario", "Máximo una agencia activa
por propietario", "Revocación de la relación agencia-propietario por el
propietario" and "Agente responsable reasignable", tasks 1.2-1.7 of
`openspec/changes/hu-007/tasks.md`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from shared.domain.exceptions import DomainValidationError


class EstadoRelacion(StrEnum):
    """Lifecycle states of a `RelacionAgenciaPropietario`.

    - `PENDIENTE`: created by the propietario, awaiting activation; the only
      state assigned at creation time.
    - `ACTIVA`: the relación is in effect.
    - `REVOCADA`: ended by the propietario; terminal state.
    """

    PENDIENTE = "pendiente"
    ACTIVA = "activa"
    REVOCADA = "revocada"


@dataclass
class RelacionAgenciaPropietario:
    """Relationship between an `Agencia` and a propietario.

    Instances must be built through `RelacionAgenciaPropietario.crear`, which
    always starts the entity in `EstadoRelacion.PENDIENTE` with
    `agente_responsable_id is None`.

    `id` is `None` until a repository assigns one on insert — same pattern as
    `Inmueble.crear` in `inmuebles/domain/inmueble.py`.
    """

    agencia_id: uuid.UUID
    propietario_id: uuid.UUID
    estado: EstadoRelacion
    agente_responsable_id: uuid.UUID | None = None
    id: uuid.UUID | None = None

    @classmethod
    def crear(
        cls, *, agencia_id: uuid.UUID, propietario_id: uuid.UUID
    ) -> RelacionAgenciaPropietario:
        """Create a new relación in `EstadoRelacion.PENDIENTE`."""
        return cls(
            agencia_id=agencia_id,
            propietario_id=propietario_id,
            estado=EstadoRelacion.PENDIENTE,
        )

    def activar(self) -> None:
        """Transition `PENDIENTE -> ACTIVA`.

        Raises `DomainValidationError` when called from any other state,
        leaving `estado` unchanged.
        """
        if self.estado != EstadoRelacion.PENDIENTE:
            raise DomainValidationError(
                f"cannot activar a relacion in estado {self.estado}, expected "
                f"{EstadoRelacion.PENDIENTE}"
            )
        self.estado = EstadoRelacion.ACTIVA

    def revocar(self) -> None:
        """Transition `ACTIVA -> REVOCADA`.

        Raises `DomainValidationError` when called from any other state,
        leaving `estado` unchanged.
        """
        if self.estado != EstadoRelacion.ACTIVA:
            raise DomainValidationError(
                f"cannot revocar a relacion in estado {self.estado}, expected "
                f"{EstadoRelacion.ACTIVA}"
            )
        self.estado = EstadoRelacion.REVOCADA

    def reasignar_responsable(self, nuevo_agente_id: uuid.UUID) -> None:
        """Overwrite `agente_responsable_id` in place, without touching `estado`.

        Reassignment is traceability-only, per design.md decisión — checking
        whether `nuevo_agente_id` is a member of this relación's agencia
        belongs to the `reasignar_responsable` use case (task 3.18), not to
        this entity method.
        """
        self.agente_responsable_id = nuevo_agente_id
