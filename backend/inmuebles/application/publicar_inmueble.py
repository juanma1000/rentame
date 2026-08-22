"""`publicar_inmueble` use case.

Orchestrates the "Creación de publicación de inmueble" / "Carga de fotos en
la publicación" / "Estado inicial de la publicación" requirements of
`openspec/changes/hu-001/specs/inmuebles/spec.md` (tasks 3.1-3.2, 4.1 of
`openspec/changes/hu-001/tasks.md`).

This module only orchestrates: it uploads photo bytes via `StoragePort`,
delegates every field/photo-count validation to `Inmueble.crear` (it must
NOT re-implement any of those rules), and persists the result via
`InmuebleRepositoryPort`.

Bug fix: the photo count is checked here, before any upload happens, purely
as a fail-fast guard against orphaned objects in S3/MinIO. Previously every
photo was uploaded first and `Inmueble.crear` validated the count only
afterwards, so an out-of-range submission (e.g. 11 photos) still left
already-uploaded objects behind in storage even though creation failed. This
check duplicates none of `Inmueble.crear`'s other rules (valor_mensual,
habitaciones, banos, ...) — those keep living exclusively in the domain —
and `Inmueble.crear` still re-validates the same count afterwards, so the
domain invariant remains enforced in exactly one place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import MAX_FOTOS_INMUEBLE, MIN_FOTOS_INMUEBLE, Inmueble
from inmuebles.domain.ports import InmuebleRepositoryPort, StoragePort
from shared.domain.exceptions import DomainValidationError


@dataclass
class FotoParaPublicar:
    """One photo's raw bytes as received from the multipart request, before
    any upload happens."""

    contenido: bytes
    es_principal: bool


@dataclass
class PublicarInmuebleCommand:
    """Every field `Inmueble.crear` needs, plus the raw photos to upload.

    `agente_id` (hu-002, design.md decisión 2/4) is optional: when an
    agente publishes on behalf of a propietario, the API layer resolves and
    passes it here; it is stored on the resulting `Inmueble` with no extra
    validation in this use case (that lives in `Inmueble.crear`)."""

    propietario_id: uuid.UUID
    direccion: str
    barrio: str
    ciudad: str
    tipo: str
    area_m2: Decimal
    habitaciones: int
    banos: int
    valor_mensual: Decimal
    descripcion: str
    fotos: list[FotoParaPublicar]
    agente_id: uuid.UUID | None = None


async def publicar_inmueble(
    command: PublicarInmuebleCommand,
    *,
    repository: InmuebleRepositoryPort,
    storage: StoragePort,
) -> Inmueble:
    """Upload `command.fotos`, create the `Inmueble` and persist it.

    Raises `DomainValidationError` when the photo count is out of range
    (checked here, before any upload, to avoid orphaned objects in storage)
    or when any other field is invalid (propagated from `Inmueble.crear`,
    which still re-validates the count too). In either case no photo upload
    that hasn't already happened is attempted, and `repository.guardar` is
    never called.
    """
    if not (MIN_FOTOS_INMUEBLE <= len(command.fotos) <= MAX_FOTOS_INMUEBLE):
        raise DomainValidationError(
            f"fotos count must be between {MIN_FOTOS_INMUEBLE} and "
            f"{MAX_FOTOS_INMUEBLE}, got {len(command.fotos)}"
        )

    upload_id = uuid.uuid4()
    fotos: list[FotoInmueble] = []
    for orden, foto in enumerate(command.fotos, start=1):
        storage_key = await storage.subir_foto(upload_id, foto.contenido, orden)
        fotos.append(
            FotoInmueble(
                url_storage=storage.construir_url(storage_key),
                storage_key=storage_key,
                orden=orden,
                es_principal=foto.es_principal,
            )
        )

    inmueble = Inmueble.crear(
        propietario_id=command.propietario_id,
        direccion=command.direccion,
        barrio=command.barrio,
        ciudad=command.ciudad,
        tipo=command.tipo,
        area_m2=command.area_m2,
        habitaciones=command.habitaciones,
        banos=command.banos,
        valor_mensual=command.valor_mensual,
        descripcion=command.descripcion,
        fotos=fotos,
        agente_id=command.agente_id,
    )

    return await repository.guardar(inmueble)
