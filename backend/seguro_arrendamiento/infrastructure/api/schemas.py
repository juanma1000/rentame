"""Pydantic schemas for the `seguro-arrendamiento` HTTP API (task 5.3).

`POST /seguro-arrendamiento/contratar` receives `multipart/form-data`
(cédula as a `Form` field, documentos as `File` parts) directly in the
router's signature — no request schema is needed for it, same convention
`identidad`'s `POST /identidad/validar` already uses. Only the response is
modeled here, built from the domain entity via `from_domain`, following the
`ValidarIdentidadResponse` precedent
(`identidad/infrastructure/api/schemas.py`) — the API layer never leaks the
SQLAlchemy model.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from seguro_arrendamiento.domain.poliza_arrendamiento import EstadoPoliza, PolizaArrendamiento


class ContratarSeguroArrendamientoResponse(BaseModel):
    """Response body returned by `POST /seguro-arrendamiento/contratar`."""

    id: uuid.UUID
    estado: EstadoPoliza
    prima_mensual: float | None
    referencia_externa: str | None

    @classmethod
    def from_domain(cls, poliza: PolizaArrendamiento) -> ContratarSeguroArrendamientoResponse:
        if poliza.id is None:
            raise ValueError(
                "cannot build ContratarSeguroArrendamientoResponse from a "
                "PolizaArrendamiento without an id"
            )
        return cls(
            id=poliza.id,
            estado=poliza.estado,
            prima_mensual=poliza.prima_mensual,
            referencia_externa=poliza.referencia_externa,
        )


class EstadoSeguroResponse(BaseModel):
    """Response body returned by `GET /seguro-arrendamiento/estado` (task
    2.4 of `openspec/changes/frontend-flujo-arrendamiento/tasks.md`).

    `estado` is a plain `str` (not `EstadoPoliza`) since it can also hold
    the synthetic `"no_iniciado"` value produced by
    `seguro_arrendamiento.application.consultar_estado_seguro` when the
    account has no `PolizaArrendamiento` yet — a value that is not a
    member of that enum, per design.md decisión 6.
    """

    estado: str
    prima_mensual: float | None = None


__all__ = ["EstadoPoliza", "ContratarSeguroArrendamientoResponse", "EstadoSeguroResponse"]
