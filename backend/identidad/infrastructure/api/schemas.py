"""Pydantic schemas for the `identidad` HTTP API (task 5.3).

`POST /identidad/validar` receives `multipart/form-data` (cédula as a
`Form` field, images as `File` parts) directly in the router's signature —
no request schema is needed for it, same convention `inmuebles`' photo
upload endpoint already uses. Only the response is modeled here, built
from the domain entity via `from_domain`, following the `AgenciaResponse`
precedent (`agencias/infrastructure/api/schemas.py`) — the API layer never
leaks the SQLAlchemy model.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from identidad.domain.validacion_identidad import EstadoValidacion, ValidacionIdentidad


class ValidarIdentidadResponse(BaseModel):
    """Response body returned by `POST /identidad/validar`."""

    id: uuid.UUID
    estado: EstadoValidacion
    referencia_externa: str | None

    @classmethod
    def from_domain(cls, validacion: ValidacionIdentidad) -> ValidarIdentidadResponse:
        if validacion.id is None:
            raise ValueError(
                "cannot build ValidarIdentidadResponse from a ValidacionIdentidad without an id"
            )
        return cls(
            id=validacion.id,
            estado=validacion.estado,
            referencia_externa=validacion.referencia_externa,
        )


__all__ = ["EstadoValidacion", "ValidarIdentidadResponse"]
