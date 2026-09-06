"""Pydantic schemas for the `pagos` HTTP API (tasks 7.2/7.4/7.6).

Follows the `ContratoResponse` precedent
(`firma_contrato/infrastructure/api/schemas.py`) — the API layer never
leaks the SQLAlchemy model, every response is built from the domain
entity via `from_domain`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from pagos.domain.pago import EstadoPago, Pago


class PagoResponse(BaseModel):
    """Response body shared by every `pagos` endpoint that returns a
    single `Pago`."""

    id: uuid.UUID
    arrendamiento_activo_id: uuid.UUID
    estado: EstadoPago
    monto: float
    fecha_limite: date
    fecha_pago: datetime | None
    referencia_externa: str | None

    @classmethod
    def from_domain(cls, pago: Pago) -> PagoResponse:
        if pago.id is None:
            raise ValueError("cannot build PagoResponse from a Pago without an id")
        return cls(
            id=pago.id,
            arrendamiento_activo_id=pago.arrendamiento_activo_id,
            estado=pago.estado,
            monto=pago.monto,
            fecha_limite=pago.fecha_limite,
            fecha_pago=pago.fecha_pago,
            referencia_externa=pago.referencia_externa,
        )


class WebhookPagoRequest(BaseModel):
    """Request body for `POST /pagos/webhook`, the payload a pasarela de
    pagos (Wompi in prod, simulated in tests) posts once a cobro reaches a
    resultado."""

    referencia_externa: str
    estado: str


class HistorialPagosResponse(BaseModel):
    """Response body for `GET /arrendamientos/{id}/pagos` — every `Pago`
    of that arrendamiento, any estado (spec.md: "sin filtrar por
    estado")."""

    pagos: list[PagoResponse]


__all__ = [
    "EstadoPago",
    "PagoResponse",
    "WebhookPagoRequest",
    "HistorialPagosResponse",
]
