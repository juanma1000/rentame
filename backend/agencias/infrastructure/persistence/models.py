"""SQLAlchemy 2.0 async ORM models for the `agencias` domain.

Maps 1:1 to the `agencia` / `solicitud_ingreso_agencia` /
`relacion_agencia_propietario` tables (task 5.1 of
`openspec/changes/hu-007/tasks.md`). Mirrors the style already established
by `inmuebles/infrastructure/persistence/models.py` (SQLAlchemy 2.0
`Mapped`/`mapped_column`, `postgresql.UUID(as_uuid=True)` primary keys,
`server_default func.now()` timestamps).

These are pure persistence models — mapping to/from the `Agencia` /
`SolicitudIngreso` / `RelacionAgenciaPropietario` domain entities happens in
`agencias/infrastructure/persistence/repository.py`, never here.

Per `design.md` decisión 2, agente-agencia membership is NOT modeled here as
a join table — it lives on `usuario.agencia_id`
(`usuarios/infrastructure/persistence/models.py`).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class AgenciaORM(Base):
    __tablename__ = "agencia"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nit: Mapped[str] = mapped_column(String(50), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SolicitudIngresoAgenciaORM(Base):
    __tablename__ = "solicitud_ingreso_agencia"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agencia_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("agencia.id"), nullable=False
    )
    agente_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RelacionAgenciaPropietarioORM(Base):
    __tablename__ = "relacion_agencia_propietario"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agencia_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("agencia.id"), nullable=False
    )
    propietario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    agente_responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
