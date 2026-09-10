"""SQLAlchemy 2.0 async ORM models for the `inmuebles` domain.

Maps 1:1 to the `inmueble`/`foto_inmueble` tables described by the
`INMUEBLE`/`FOTO_INMUEBLE` entities in `docs/architecture/architecture.md`
(section 2, ER diagram). Mirrors the style already established by
`usuarios/infrastructure/persistence/models.py` (SQLAlchemy 2.0 `Mapped`/
`mapped_column`, `postgresql.UUID(as_uuid=True)` primary keys, `server_default
func.now()` timestamps).

These are pure persistence models — mapping to/from the `Inmueble`/
`FotoInmueble` domain entities happens in
`inmuebles/infrastructure/persistence/repository.py`, never here.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database import Base


class InmuebleORM(Base):
    __tablename__ = "inmueble"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    propietario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    agente_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    barrio: Mapped[str] = mapped_column(String(255), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    area_m2: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    habitaciones: Mapped[int] = mapped_column(Integer, nullable=False)
    banos: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    fotos: Mapped[list["FotoInmuebleORM"]] = relationship(
        "FotoInmuebleORM",
        back_populates="inmueble",
        cascade="all, delete-orphan",
        order_by="FotoInmuebleORM.orden",
    )


class FotoInmuebleORM(Base):
    __tablename__ = "foto_inmueble"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inmueble_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("inmueble.id", ondelete="CASCADE"),
        nullable=False,
    )
    url_storage: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    inmueble: Mapped[InmuebleORM] = relationship("InmuebleORM", back_populates="fotos")
