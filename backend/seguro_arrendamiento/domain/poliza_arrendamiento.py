"""`PolizaArrendamiento` aggregate.

Business rules come from
`openspec/changes/seguro-arrendamiento-inquilino/specs/seguro-arrendamiento/spec.md`
(Requirement: "Resultado modelado como póliza con estado propio") and task
1.1-1.2 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`.

Unlike `identidad.domain.validacion_identidad.ValidacionIdentidad` (a
punctual approved/rejected event), this aggregate models a continuing
relationship — design.md decisión 2 — with its own vigencia and a
`prima_mensual` other domains (HU-006, not built yet) will read repeatedly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum

from seguro_arrendamiento.domain.exceptions import PolizaRechazadaNoPuedeActivarse


class EstadoPoliza(str, Enum):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    ACTIVA = "activa"
    VENCIDA = "vencida"


@dataclass
class PolizaArrendamiento:
    """A single seguro de arrendamiento contratación, and its subsequent
    lifecycle (`aprobada` -> `activa` -> `vencida`).

    Instances must be built through `PolizaArrendamiento.solicitar`. `id` is
    `None` until a repository assigns one on insert — same pattern as
    `ValidacionIdentidad`/`Agencia.crear`.
    """

    usuario_id: uuid.UUID
    estado: EstadoPoliza
    fecha: datetime
    prima_mensual: float | None = None
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None
    referencia_externa: str | None = None
    id: uuid.UUID | None = None

    @classmethod
    def solicitar(cls, *, usuario_id: uuid.UUID) -> PolizaArrendamiento:
        """Start a new `PolizaArrendamiento` in estado `pendiente`, awaiting
        the proveedor's response."""
        return cls(
            usuario_id=usuario_id,
            estado=EstadoPoliza.PENDIENTE,
            fecha=datetime.now(timezone.utc),
        )

    def aprobar(
        self,
        *,
        prima_mensual: float,
        vigencia_desde: date,
        vigencia_hasta: date,
        referencia_externa: str,
    ) -> None:
        """Transition this póliza to estado `aprobada`, per spec.md's
        "Póliza aprobada queda registrada con prima y vigencia"."""
        self.estado = EstadoPoliza.APROBADA
        self.prima_mensual = prima_mensual
        self.vigencia_desde = vigencia_desde
        self.vigencia_hasta = vigencia_hasta
        self.referencia_externa = referencia_externa
        self.fecha = datetime.now(timezone.utc)

    def rechazar(self, *, referencia_externa: str | None) -> None:
        """Transition this póliza to estado `rechazada`, per spec.md's
        "Póliza rechazada queda registrada" — still recorded for audit,
        without habilitar avance."""
        self.estado = EstadoPoliza.RECHAZADA
        self.referencia_externa = referencia_externa
        self.fecha = datetime.now(timezone.utc)

    def activar(self) -> None:
        """Transition an `aprobada` póliza to `activa`.

        Raises `PolizaRechazadaNoPuedeActivarse` when called on a
        `rechazada` póliza — the invariant fixed by design.md's testing
        strategy.
        """
        if self.estado == EstadoPoliza.RECHAZADA:
            raise PolizaRechazadaNoPuedeActivarse(
                "Una póliza rechazada no puede activarse"
            )
        self.estado = EstadoPoliza.ACTIVA
        self.fecha = datetime.now(timezone.utc)

    def vencer(self) -> None:
        """Transition an `activa` póliza to `vencida`."""
        self.estado = EstadoPoliza.VENCIDA
        self.fecha = datetime.now(timezone.utc)

    def habilita_continuar(self) -> bool:
        """Per spec.md's "Póliza aprobada habilita continuar hacia la firma
        del contrato": `True` when this póliza is `aprobada` or `activa`."""
        return self.estado in (EstadoPoliza.APROBADA, EstadoPoliza.ACTIVA)
