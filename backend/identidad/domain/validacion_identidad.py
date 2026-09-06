"""`ValidacionIdentidad` entity.

Business rules come from
`openspec/changes/validacion-identidad-inquilino/specs/identidad/spec.md`
(Requirements: "Validación de identidad vía cédula colombiana", "Resultado
de validación contra proveedor externo", "Una sola validación exitosa por
cuenta") and task 1.1 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from identidad.domain.exceptions import IdentidadYaVerificada


class EstadoValidacion(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


@dataclass
class ValidacionIdentidad:
    """A single attempt at validating an inquilino's identity via cédula.

    Instances must be built through `ValidacionIdentidad.iniciar`, which
    enforces the "una sola validación aprobada por cuenta" invariant up
    front. Every attempt (approved or rejected) is kept — per design.md's
    testing strategy, a rejected attempt is still persisted for audit,
    it just never marks `Usuario.identidad_verificada`.

    `id` is `None` until a repository assigns one on insert — same pattern
    as `Agencia.crear`/`Inmueble.crear`.
    """

    usuario_id: uuid.UUID
    cedula: str
    estado: EstadoValidacion
    fecha: datetime
    referencia_externa: str | None = None
    id: uuid.UUID | None = None

    @classmethod
    def iniciar(
        cls,
        *,
        usuario_id: uuid.UUID,
        cedula: str,
        validaciones_existentes: list[ValidacionIdentidad],
    ) -> ValidacionIdentidad:
        """Start a new validación attempt in estado `pendiente`.

        Raises `IdentidadYaVerificada` when `validaciones_existentes`
        already contains one in estado `aprobado` — the invariant "una sola
        validación aprobada por cuenta" (spec.md). No instance is returned
        in that case, so no proveedor externo call should ever be made
        beyond this point for that account.
        """
        if any(v.estado == EstadoValidacion.APROBADO for v in validaciones_existentes):
            raise IdentidadYaVerificada(
                f"La cuenta {usuario_id} ya tiene una validación de identidad aprobada"
            )

        return cls(
            usuario_id=usuario_id,
            cedula=cedula,
            estado=EstadoValidacion.PENDIENTE,
            fecha=datetime.now(timezone.utc),
        )

    def aprobar(self, *, referencia_externa: str) -> None:
        """Transition this validación to estado `aprobado`."""
        self.estado = EstadoValidacion.APROBADO
        self.referencia_externa = referencia_externa
        self.fecha = datetime.now(timezone.utc)

    def rechazar(self, *, referencia_externa: str | None) -> None:
        """Transition this validación to estado `rechazado`.

        Still recorded with `referencia_externa` when the proveedor gave
        one, per design.md's audit trail requirement.
        """
        self.estado = EstadoValidacion.RECHAZADO
        self.referencia_externa = referencia_externa
        self.fecha = datetime.now(timezone.utc)
