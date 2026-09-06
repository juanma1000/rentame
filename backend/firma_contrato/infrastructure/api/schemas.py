"""Pydantic schemas for the `firma-contrato` HTTP API (tasks 6.2/6.4).

Follows the `ContratarSeguroArrendamientoResponse` precedent
(`seguro_arrendamiento/infrastructure/api/schemas.py`) — the API layer
never leaks the SQLAlchemy model, every response is built from the domain
entity via `from_domain`.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from firma_contrato.domain.contrato import Contrato, EstadoContrato


class GenerarContratoRequest(BaseModel):
    """Request body for `POST /firma-contrato/generar`.

    `usuario_id` is deliberately absent here — it comes from the JWT
    (`get_current_inquilino`), same convention as
    `seguro_arrendamiento`'s `contratar` endpoint.
    """

    inmueble_id: uuid.UUID
    nombre_inquilino: str
    nombre_propietario: str
    direccion_inmueble: str
    canon_mensual: float
    duracion_meses: int


class ContratoResponse(BaseModel):
    """Response body returned by `POST /firma-contrato/generar`."""

    id: uuid.UUID
    estado: EstadoContrato
    referencia_externa: str | None

    @classmethod
    def from_domain(cls, contrato: Contrato) -> ContratoResponse:
        if contrato.id is None:
            raise ValueError("cannot build ContratoResponse from a Contrato without an id")
        return cls(
            id=contrato.id,
            estado=contrato.estado,
            referencia_externa=contrato.referencia_externa,
        )


class WebhookFirmaRequest(BaseModel):
    """Request body for `POST /firma-contrato/webhook`, the payload a
    proveedor de firma electrónica (Viafirma in prod, simulated in tests)
    posts once a firma process reaches a resultado."""

    referencia_externa: str
    estado: str


__all__ = [
    "EstadoContrato",
    "GenerarContratoRequest",
    "ContratoResponse",
    "WebhookFirmaRequest",
]
