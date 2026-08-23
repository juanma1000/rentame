"""Synthetic seed data for local development.

Populates `usuario`, `agencia`, `solicitud_ingreso_agencia`,
`relacion_agencia_propietario`, `inmueble` and `foto_inmueble` (with real
placeholder images uploaded to MinIO) so the local environment is never
empty. Uses the same domain factories/repositories the application uses —
no data is inserted that the domain would reject.

Idempotent: every seeded row's owning email ends in `@seed.rentame.test`;
re-running first deletes every previously-seeded row (and their MinIO
objects) before inserting fresh ones.

Run with:
    docker compose exec backend python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import struct
import uuid
import zlib
from decimal import Decimal

import boto3
from botocore.client import Config
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agencias.domain.agencia import Agencia
from agencias.domain.relacion_agencia_propietario import RelacionAgenciaPropietario
from agencias.domain.solicitud_ingreso import SolicitudIngreso
from agencias.infrastructure.persistence.models import (
    AgenciaORM,
    RelacionAgenciaPropietarioORM,
    SolicitudIngresoAgenciaORM,
)
from agencias.infrastructure.persistence.repository import (
    AgenciaRepositoryPostgres,
    RelacionRepositoryPostgres,
    SolicitudIngresoRepositoryPostgres,
)
from inmuebles.domain.foto import FotoInmueble
from inmuebles.domain.inmueble import Inmueble
from inmuebles.infrastructure.persistence.models import FotoInmuebleORM, InmuebleORM
from inmuebles.infrastructure.persistence.repository import InmuebleRepositoryPostgres
from shared.infrastructure.auth.jwt_handler import create_access_token
from shared.infrastructure.database import AsyncSessionLocal
from shared.infrastructure.settings import get_settings
from usuarios.domain.usuario import Usuario
from usuarios.infrastructure.persistence.models import UsuarioORM

SEED_EMAIL_SUFFIX = "@seed.rentame.test"
SEED_PASSWORD = "Seed1234!"


def _png_placeholder(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Build a valid, solid-color PNG with no external dependencies."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(rgb) * width
    raw_scanlines = row * height
    idat = zlib.compress(raw_scanlines)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


async def _subir_foto_placeholder(
    s3_client, bucket: str, endpoint: str, inmueble_id: uuid.UUID, rgb: tuple[int, int, int]
) -> tuple[str, str]:
    """Upload a placeholder PNG and return `(storage_key, url_storage)`."""
    storage_key = f"inmuebles/{inmueble_id}/{uuid.uuid4()}.png"
    contenido = _png_placeholder(640, 480, rgb)
    await asyncio.to_thread(
        s3_client.put_object,
        Bucket=bucket,
        Key=storage_key,
        Body=contenido,
        ContentType="image/png",
    )
    url_storage = f"{endpoint.rstrip('/')}/{bucket}/{storage_key}"
    return storage_key, url_storage


async def _borrar_seed_previo(session: AsyncSession, s3_client, bucket: str) -> None:
    """Delete every row/object created by a previous run of this script."""
    usuarios_previos = (
        await session.execute(
            select(UsuarioORM.id).where(UsuarioORM.email.like(f"%{SEED_EMAIL_SUFFIX}"))
        )
    ).scalars().all()
    if not usuarios_previos:
        return

    inmuebles_previos = (
        await session.execute(
            select(InmuebleORM.id).where(InmuebleORM.propietario_id.in_(usuarios_previos))
        )
    ).scalars().all()
    if inmuebles_previos:
        fotos_previas = (
            await session.execute(
                select(FotoInmuebleORM.storage_key).where(
                    FotoInmuebleORM.inmueble_id.in_(inmuebles_previos)
                )
            )
        ).scalars().all()
        for storage_key in fotos_previas:
            await asyncio.to_thread(s3_client.delete_object, Bucket=bucket, Key=storage_key)
        await session.execute(delete(InmuebleORM).where(InmuebleORM.id.in_(inmuebles_previos)))

    await session.execute(
        delete(RelacionAgenciaPropietarioORM).where(
            RelacionAgenciaPropietarioORM.propietario_id.in_(usuarios_previos)
        )
    )
    await session.execute(
        delete(SolicitudIngresoAgenciaORM).where(
            SolicitudIngresoAgenciaORM.agente_id.in_(usuarios_previos)
        )
    )
    await session.execute(
        delete(UsuarioORM)
        .where(UsuarioORM.id.in_(usuarios_previos))
        .execution_options(synchronize_session=False)
    )
    agencias_previas = (
        await session.execute(
            select(AgenciaORM.id).where(AgenciaORM.nit.like("SEED-%"))
        )
    ).scalars().all()
    if agencias_previas:
        await session.execute(delete(AgenciaORM).where(AgenciaORM.id.in_(agencias_previas)))

    await session.flush()


async def seed() -> None:
    settings = get_settings()
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name=settings.storage_region,
        config=Config(signature_version="s3v4"),
    )
    bucket = settings.storage_bucket_name

    async with AsyncSessionLocal() as session:
        await _borrar_seed_previo(session, s3_client, bucket)

        usuario_repo_ids: dict[str, uuid.UUID] = {}

        def _nuevo_usuario(email_local: str, rol: str) -> UsuarioORM:
            usuario = Usuario.crear(
                email=f"{email_local}{SEED_EMAIL_SUFFIX}",
                password=SEED_PASSWORD,
                nombre=email_local.replace(".", " ").title(),
                rol=rol,
            )
            modelo = UsuarioORM(
                email=usuario.email,
                password_hash=usuario.password_hash,
                nombre=usuario.nombre,
                rol=usuario.rol,
            )
            session.add(modelo)
            return modelo

        ana = _nuevo_usuario("ana.propietaria", "propietario")
        carlos = _nuevo_usuario("carlos.propietario", "propietario")
        laura = _nuevo_usuario("laura.agente", "agente")
        pedro = _nuevo_usuario("pedro.agente", "agente")
        sofia = _nuevo_usuario("sofia.inquilino", "inquilino")
        diego = _nuevo_usuario("diego.inquilino", "inquilino")
        await session.flush()

        agencia_repo = AgenciaRepositoryPostgres(session)
        agencia = await agencia_repo.guardar(
            Agencia.crear(razon_social="Inmobiliaria del Valle SAS", nit="SEED-900123456-1")
        )
        laura.agencia_id = agencia.id
        await session.flush()

        relacion_repo = RelacionRepositoryPostgres(session)
        relacion = RelacionAgenciaPropietario.crear(
            agencia_id=agencia.id, propietario_id=carlos.id
        )
        relacion.activar()
        relacion.reasignar_responsable(laura.id)
        await relacion_repo.guardar(relacion)

        solicitud_repo = SolicitudIngresoRepositoryPostgres(session)
        await solicitud_repo.guardar(
            SolicitudIngreso.crear(agencia_id=agencia.id, agente_id=pedro.id)
        )

        inmueble_repo = InmuebleRepositoryPostgres(session)

        async def _crear_inmueble(
            *,
            propietario_id: uuid.UUID,
            agente_id: uuid.UUID | None,
            direccion: str,
            barrio: str,
            ciudad: str,
            tipo: str,
            area_m2: str,
            habitaciones: int,
            banos: int,
            valor_mensual: str,
            descripcion: str,
            colores: list[tuple[int, int, int]],
            oculto: bool = False,
        ) -> InmuebleORM:
            inmueble_id = uuid.uuid4()
            fotos = []
            for orden, rgb in enumerate(colores, start=1):
                storage_key, url_storage = await _subir_foto_placeholder(
                    s3_client,
                    bucket,
                    settings.storage_public_url or settings.storage_endpoint_url,
                    inmueble_id,
                    rgb,
                )
                fotos.append(
                    FotoInmueble(
                        url_storage=url_storage,
                        storage_key=storage_key,
                        orden=orden,
                        es_principal=(orden == 1),
                    )
                )
            inmueble = Inmueble.crear(
                propietario_id=propietario_id,
                agente_id=agente_id,
                direccion=direccion,
                barrio=barrio,
                ciudad=ciudad,
                tipo=tipo,
                area_m2=Decimal(area_m2),
                habitaciones=habitaciones,
                banos=banos,
                valor_mensual=Decimal(valor_mensual),
                descripcion=descripcion,
                fotos=fotos,
            )
            inmueble.id = inmueble_id
            if oculto:
                inmueble.despublicar()
            guardado = await inmueble_repo.guardar(inmueble)
            return guardado

        await _crear_inmueble(
            propietario_id=ana.id,
            agente_id=None,
            direccion="Calle 10 # 5-30",
            barrio="El Poblado",
            ciudad="Medellín",
            tipo="apartamento",
            area_m2="72.5",
            habitaciones=2,
            banos=2,
            valor_mensual="2200000",
            descripcion="Apartamento luminoso cerca al parque, remodelado en 2024.",
            colores=[(200, 60, 60), (60, 120, 200)],
        )
        await _crear_inmueble(
            propietario_id=ana.id,
            agente_id=None,
            direccion="Carrera 45 # 12-08",
            barrio="Laureles",
            ciudad="Medellín",
            tipo="apartaestudio",
            area_m2="38.0",
            habitaciones=1,
            banos=1,
            valor_mensual="1350000",
            descripcion="Apartaestudio ideal para una persona, cerca a universidades.",
            colores=[(90, 180, 90)],
        )
        await _crear_inmueble(
            propietario_id=carlos.id,
            agente_id=laura.id,
            direccion="Avenida 80 # 34-21",
            barrio="Belén",
            ciudad="Medellín",
            tipo="casa",
            area_m2="145.0",
            habitaciones=4,
            banos=3,
            valor_mensual="3800000",
            descripcion="Casa de dos plantas con patio, gestionada por Inmobiliaria del Valle.",
            colores=[(220, 170, 40), (40, 200, 200), (150, 90, 200)],
        )
        await _crear_inmueble(
            propietario_id=carlos.id,
            agente_id=laura.id,
            direccion="Calle 33 # 70-15",
            barrio="Robledo",
            ciudad="Medellín",
            tipo="apartamento",
            area_m2="55.0",
            habitaciones=2,
            banos=1,
            valor_mensual="1600000",
            descripcion="Apartamento temporalmente despublicado por el propietario.",
            colores=[(120, 120, 120)],
            oculto=True,
        )

        await session.commit()

    print(f"Seed completado. Contraseña de todos los usuarios de prueba: {SEED_PASSWORD}\n")
    for usuario in (ana, carlos, laura, pedro, sofia, diego):
        token = create_access_token(str(usuario.id), usuario.rol)
        print(f"- {usuario.email} [{usuario.rol}] id={usuario.id}")
        print(f"  Authorization: Bearer {token}\n")


if __name__ == "__main__":
    asyncio.run(seed())
