"""SQLAlchemy 2.0 async ORM models for the `firma-contrato` domain.

Map 1:1 to the `contratos` and `arrendamientos_activos` tables (task 5.3 of
`openspec/changes/firma-electronica-contrato-arrendamiento/tasks.md`).
Mirrors the style already established by
`seguro_arrendamiento/infrastructure/persistence/models.py` (SQLAlchemy 2.0
`Mapped`/`mapped_column`, `postgresql.UUID(as_uuid=True)` primary keys).

`ContratoORM.inmueble_id` is not part of tasks.md's originally-listed column
set for `contratos` (usuario_id, poliza_id, estado, documento_referencia,
referencia_externa) — it is added here because `ArrendamientoActivo` must
be able to recover the inmueble a `Contrato` refers to once the webhook
reports `firmado`, and `PolizaArrendamiento` has no `inmueble_id` field to
read it back from (see `firma_contrato/domain/contrato.py`'s docstring).
This is a deliberate, reported deviation from the task's literal column
list, not an oversight.

These are pure persistence models — mapping to/from the domain entities
happens in `firma_contrato/infrastructure/persistence/repository.py`,
never here.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class ContratoORM(Base):
    __tablename__ = "contratos"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    poliza_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("polizas_arrendamiento.id"), nullable=False
    )
    inmueble_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    documento_referencia: Mapped[str] = mapped_column(String, nullable=False)
    referencia_externa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArrendamientoActivoORM(Base):
    __tablename__ = "arrendamientos_activos"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    poliza_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("polizas_arrendamiento.id"), nullable=False
    )
    contrato_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False, unique=True
    )
    inmueble_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date(), nullable=False)
