"""`Pago` aggregate.

Business rules come from
`openspec/changes/pago-mensual-renta/specs/pagos/spec.md` (Requirement:
"Resultado modelado como pago con estado propio") and task 1.1-1.2 of
`openspec/changes/pago-mensual-renta/tasks.md`.

Modeled on `firma_contrato.domain.contrato.Contrato`'s state-machine
pattern, with one deliberate difference: `EstadoPago.COMPLETADO` is the
*only* final state. `FALLIDO` is intentionally not final — spec.md's "Un
pago ya completado no puede reiniciarse" scenario only names `completado`,
and design.md's Non-Goals note the inquilino "puede iniciar un nuevo
intento manualmente" after a failed pago, with the exact mechanics left
unspecified ("no está más detallado en este change"). Allowing
`marcar_completado`/`marcar_fallido` to be called again from `FALLIDO`
(but never from `COMPLETADO`) is the smallest rule that satisfies both.

`registrar_intento` exists separately from `marcar_completado` because a
pasarela's cobro can resolve asynchronously (Wompi, per design.md's
sequence diagram: "Wompi: async, webhook luego") — `iniciar_pago` must be
able to record the pasarela's `referencia_externa` for the in-flight
attempt without prematurely marking the `Pago` `completado`; the actual
resolution arrives later via `pagos.application.procesar_resultado_pago`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum

from pagos.domain.exceptions import PagoYaCompletado


class EstadoPago(str, Enum):
    PENDIENTE = "pendiente"
    COMPLETADO = "completado"
    FALLIDO = "fallido"


@dataclass
class Pago:
    """A single cobro mensual owed by an `ArrendamientoActivo`, and its
    subsequent resolution (`pendiente` -> `completado`/`fallido`).

    Instances must be built through `Pago.crear`. `id` is `None` until a
    repository assigns one on insert — same pattern as
    `Contrato`/`PolizaArrendamiento`.
    """

    arrendamiento_activo_id: uuid.UUID
    estado: EstadoPago
    monto: float
    fecha_limite: date
    fecha_pago: datetime | None = None
    referencia_externa: str | None = None
    id: uuid.UUID | None = None

    @classmethod
    def crear(
        cls,
        *,
        arrendamiento_activo_id: uuid.UUID,
        monto: float,
        fecha_limite: date,
    ) -> Pago:
        """Start a new `Pago` in estado `pendiente`, per spec.md's
        "Generación automática del pago pendiente por ciclo"."""
        return cls(
            arrendamiento_activo_id=arrendamiento_activo_id,
            estado=EstadoPago.PENDIENTE,
            monto=monto,
            fecha_limite=fecha_limite,
        )

    def _asegurar_no_completado(self) -> None:
        if self.estado == EstadoPago.COMPLETADO:
            raise PagoYaCompletado(
                f"El pago {self.id} ya está completado y no puede cambiar de estado"
            )

    def registrar_intento(self, *, referencia_externa: str) -> None:
        """Record the pasarela's `referencia_externa` for the cobro
        attempt just started, without changing `estado` — used when the
        pasarela's result is asynchronous and the actual resolution
        arrives later via the webhook.

        Raises `PagoYaCompletado` when this `Pago` is already
        `completado`.
        """
        self._asegurar_no_completado()
        self.referencia_externa = referencia_externa

    def marcar_completado(self, *, referencia_externa: str) -> None:
        """Transition this pago to estado `completado`, per spec.md's
        "Pago completado exitosamente queda registrado".

        Raises `PagoYaCompletado` when this `Pago` is already
        `completado` — the invariant fixed by spec.md's "Un pago ya
        completado no puede reiniciarse".
        """
        self._asegurar_no_completado()
        self.estado = EstadoPago.COMPLETADO
        self.referencia_externa = referencia_externa
        self.fecha_pago = datetime.now(UTC)

    def marcar_fallido(self, *, referencia_externa: str) -> None:
        """Transition this pago to estado `fallido`, per spec.md's "Pago
        fallido queda registrado" — `fecha_pago` is left unset.

        Raises `PagoYaCompletado` when this `Pago` is already
        `completado`.
        """
        self._asegurar_no_completado()
        self.estado = EstadoPago.FALLIDO
        self.referencia_externa = referencia_externa
