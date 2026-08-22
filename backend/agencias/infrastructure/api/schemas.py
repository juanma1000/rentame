"""Pydantic schemas for the `agencias` HTTP API (task 7.1).

Every `*Response` is built from the corresponding domain entity via a
`from_domain` classmethod, following the `InmuebleResponse` precedent
(`inmuebles/infrastructure/api/schemas.py`) — the API layer never leaks
SQLAlchemy models nor the raw dataclass.

Endpoints without a request body (`solicitudes`, `aprobar`, `salir`,
`relaciones`, `confirmar`, `revocar`) do not need a request schema — only
`AgenciaCreateRequest` (`POST /agencias/`) and
`ReasignarResponsableRequest` (`PATCH .../responsable`) carry a JSON body,
per the contract fixed by `tests/agencias/infrastructure/test_api.py`.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import (
    EstadoRelacion,
    RelacionAgenciaPropietario,
)
from agencias.domain.solicitud_ingreso import EstadoSolicitudIngreso, SolicitudIngreso


class AgenciaCreateRequest(BaseModel):
    """JSON body accepted by `POST /agencias/`."""

    razon_social: str
    nit: str


class AgenciaResponse(BaseModel):
    """Response body returned by `POST /agencias/`."""

    id: uuid.UUID
    razon_social: str
    nit: str

    @classmethod
    def from_domain(cls, agencia: Agencia) -> AgenciaResponse:
        if agencia.id is None:
            raise ValueError("cannot build AgenciaResponse from an Agencia without an id")
        return cls(id=agencia.id, razon_social=agencia.razon_social, nit=agencia.nit)


class AgenciaBuscarResponse(BaseModel):
    """Response body item returned by `GET /agencias/buscar` — public endpoint,
    so only the fields already exposed by `AgenciaResponse` are included
    (no `Agencia` field is actually sensitive today, but this schema is kept
    separate so a future non-public field added to `Agencia` never leaks here
    by accident)."""

    id: uuid.UUID
    razon_social: str
    nit: str

    @classmethod
    def from_domain(cls, agencia: Agencia) -> AgenciaBuscarResponse:
        if agencia.id is None:
            raise ValueError("cannot build AgenciaBuscarResponse from an Agencia without an id")
        return cls(id=agencia.id, razon_social=agencia.razon_social, nit=agencia.nit)


class SolicitudIngresoResponse(BaseModel):
    """Response body shared by `POST /agencias/{id}/solicitudes` and
    `POST /agencias/solicitudes/{id}/aprobar`."""

    id: uuid.UUID
    agencia_id: uuid.UUID
    agente_id: uuid.UUID
    estado: EstadoSolicitudIngreso

    @classmethod
    def from_domain(cls, solicitud: SolicitudIngreso) -> SolicitudIngresoResponse:
        if solicitud.id is None:
            raise ValueError(
                "cannot build SolicitudIngresoResponse from a SolicitudIngreso without an id"
            )
        return cls(
            id=solicitud.id,
            agencia_id=solicitud.agencia_id,
            agente_id=solicitud.agente_id,
            estado=solicitud.estado,
        )


class RelacionResponse(BaseModel):
    """Response body shared by every `.../relaciones` and `.../mia/propietarios`
    endpoint.

    `propietario_email` (hu-002, task 6.5) is `None` on every endpoint that
    only has the domain `RelacionAgenciaPropietario` at hand (`iniciar`,
    `confirmar`, `revocar`, `reasignar_responsable`) and populated only by
    `GET /agencias/mia/propietarios`, the one endpoint that needs to render
    a human-readable propietario selector on the frontend (hu-002 task 11.x)
    — resolved there, in the API layer, from `usuario.email` (no `agencias/
    application` or `agencias/domain` change needed for this).
    """

    id: uuid.UUID
    agencia_id: uuid.UUID
    propietario_id: uuid.UUID
    propietario_email: str | None = None
    estado: EstadoRelacion
    agente_responsable_id: uuid.UUID | None

    @classmethod
    def from_domain(
        cls,
        relacion: RelacionAgenciaPropietario,
        *,
        propietario_email: str | None = None,
    ) -> RelacionResponse:
        if relacion.id is None:
            raise ValueError(
                "cannot build RelacionResponse from a RelacionAgenciaPropietario without an id"
            )
        return cls(
            id=relacion.id,
            agencia_id=relacion.agencia_id,
            propietario_id=relacion.propietario_id,
            propietario_email=propietario_email,
            estado=relacion.estado,
            agente_responsable_id=relacion.agente_responsable_id,
        )


class ReasignarResponsableRequest(BaseModel):
    """JSON body accepted by `PATCH /agencias/relaciones/{id}/responsable`."""

    nuevo_agente_id: uuid.UUID
