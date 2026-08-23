"""Pydantic schemas for the `inmuebles` HTTP API (task 7.1).

`InmuebleResponse` is the shape returned by every endpoint (`POST`, `PUT`,
`PATCH /disponibilidad`, `GET /mios`), built from the domain `Inmueble`
entity via `InmuebleResponse.from_domain` — the API layer never leaks
SQLAlchemy models nor the raw dataclass, per the hexagonal boundary.
`InmuebleEditRequest` mirrors the editable fields accepted by `PUT` (no
`fotos` — editing photos is out of scope, see `editar_inmueble.py`).
`CambiarDisponibilidadRequest` restricts `nuevo_estado` to the two states
reachable through this HTTP endpoint (`design.md` decisión 4:
`no_disponible` is reached only by a future internal caller, never via
HTTP).

`area_m2`/`valor_mensual` are typed `float` (not `Decimal`) on
`InmuebleResponse` so they serialize as JSON numbers: Pydantic v2 serializes
`Decimal` fields to JSON *strings* by default, which would break
`test_api.py`'s `response_body["valor_mensual"] == 1500000` (str != int).

`InmuebleResponse.agente_id` (hu-002) is `None` for propietario-published
listings and the calling agente's id for agente-published/managed ones —
exposed on every endpoint's response body (`POST`, `PUT`,
`PATCH /disponibilidad`, `GET /mios`, `GET /gestionados`).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import EstadoInmueble, Inmueble


class FotoResponse(BaseModel):
    """`FotoInmueble` as exposed over HTTP, including `storage_key` (not
    just `url_storage`) so callers can address the exact object in storage."""

    url_storage: str
    storage_key: str
    orden: int
    es_principal: bool

    @classmethod
    def from_domain(cls, foto: FotoInmueble) -> FotoResponse:
        return cls(
            url_storage=foto.url_storage,
            storage_key=foto.storage_key,
            orden=foto.orden,
            es_principal=foto.es_principal,
        )


class InmuebleResponse(BaseModel):
    """Response body shape shared by every `inmuebles` endpoint."""

    id: uuid.UUID
    propietario_id: uuid.UUID
    agente_id: uuid.UUID | None
    direccion: str
    barrio: str
    ciudad: str
    tipo: str
    area_m2: float
    habitaciones: int
    banos: int
    valor_mensual: float
    descripcion: str
    estado: EstadoInmueble
    fotos: list[FotoResponse]

    @classmethod
    def from_domain(cls, inmueble: Inmueble) -> InmuebleResponse:
        if inmueble.id is None:
            raise ValueError("cannot build InmuebleResponse from an Inmueble without an id")
        return cls(
            id=inmueble.id,
            propietario_id=inmueble.propietario_id,
            agente_id=inmueble.agente_id,
            direccion=inmueble.direccion,
            barrio=inmueble.barrio,
            ciudad=inmueble.ciudad,
            tipo=inmueble.tipo,
            area_m2=float(inmueble.area_m2),
            habitaciones=inmueble.habitaciones,
            banos=inmueble.banos,
            valor_mensual=float(inmueble.valor_mensual),
            descripcion=inmueble.descripcion,
            estado=inmueble.estado,
            fotos=[FotoResponse.from_domain(foto) for foto in inmueble.fotos],
        )


class InmueblePublicoListItemResponse(BaseModel):
    """Response body item for `GET /inmuebles/publicos` (hu-003 task 3.2).

    Deliberately narrower than `InmuebleResponse`: no `propietario_id`,
    `agente_id` nor `estado` are exposed to anonymous callers. `foto_principal`
    is the `url_storage` of the inmueble's `es_principal` foto, or `None`
    when it has no photos at all.
    """

    id: uuid.UUID
    foto_principal: str | None
    direccion: str
    barrio: str
    ciudad: str
    valor_mensual: float
    habitaciones: int
    banos: int

    @classmethod
    def from_domain(cls, inmueble: Inmueble) -> InmueblePublicoListItemResponse:
        if inmueble.id is None:
            raise ValueError(
                "cannot build InmueblePublicoListItemResponse from an Inmueble without an id"
            )
        foto_principal = next(
            (foto.url_storage for foto in inmueble.fotos if foto.es_principal), None
        )
        return cls(
            id=inmueble.id,
            foto_principal=foto_principal,
            direccion=inmueble.direccion,
            barrio=inmueble.barrio,
            ciudad=inmueble.ciudad,
            valor_mensual=float(inmueble.valor_mensual),
            habitaciones=inmueble.habitaciones,
            banos=inmueble.banos,
        )


class FotoPublicaResponse(BaseModel):
    """Photo shape exposed by `GET /inmuebles/publicos/{id}` (hu-003 task
    3.4) — no `storage_key`, unlike `FotoResponse`, since anonymous callers
    only ever need the resolvable `url_storage`."""

    url_storage: str
    orden: int
    es_principal: bool

    @classmethod
    def from_domain(cls, foto: FotoInmueble) -> FotoPublicaResponse:
        return cls(
            url_storage=foto.url_storage,
            orden=foto.orden,
            es_principal=foto.es_principal,
        )


class InmueblePublicoResponse(BaseModel):
    """Response body for `GET /inmuebles/publicos/{id}` (hu-003 task 3.4).

    Like `InmueblePublicoListItemResponse`, excludes `propietario_id`,
    `agente_id` and `estado` from anonymous callers.
    """

    id: uuid.UUID
    direccion: str
    barrio: str
    ciudad: str
    tipo: str
    area_m2: float
    habitaciones: int
    banos: int
    valor_mensual: float
    descripcion: str
    fotos: list[FotoPublicaResponse]

    @classmethod
    def from_domain(cls, inmueble: Inmueble) -> InmueblePublicoResponse:
        if inmueble.id is None:
            raise ValueError("cannot build InmueblePublicoResponse from an Inmueble without an id")
        return cls(
            id=inmueble.id,
            direccion=inmueble.direccion,
            barrio=inmueble.barrio,
            ciudad=inmueble.ciudad,
            tipo=inmueble.tipo,
            area_m2=float(inmueble.area_m2),
            habitaciones=inmueble.habitaciones,
            banos=inmueble.banos,
            valor_mensual=float(inmueble.valor_mensual),
            descripcion=inmueble.descripcion,
            fotos=[FotoPublicaResponse.from_domain(foto) for foto in inmueble.fotos],
        )


class InmuebleEditRequest(BaseModel):
    """JSON body accepted by `PUT /inmuebles/{id}` — same editable data
    fields `Inmueble.actualizar_datos` accepts, no `fotos`."""

    direccion: str
    barrio: str
    ciudad: str
    tipo: str
    area_m2: Decimal
    habitaciones: int
    banos: int
    valor_mensual: Decimal
    descripcion: str


class CambiarDisponibilidadRequest(BaseModel):
    """JSON body accepted by `PATCH /inmuebles/{id}/disponibilidad`.

    `nuevo_estado` intentionally excludes `"no_disponible"` (design.md
    decisión 4): that state is only ever set by a future internal caller
    (the `arrendamiento` use case), never through this HTTP endpoint.
    """

    nuevo_estado: Literal["disponible", "oculto"]
