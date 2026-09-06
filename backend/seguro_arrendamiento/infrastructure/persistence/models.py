"""SQLAlchemy 2.0 async ORM model for the `seguro-arrendamiento` domain.

Maps 1:1 to the `polizas_arrendamiento` table (task 4.3 of
`openspec/changes/seguro-arrendamiento-inquilino/tasks.md`). Mirrors the
style already established by
`identidad/infrastructure/persistence/models.py` (SQLAlchemy 2.0
`Mapped`/`mapped_column`, `postgresql.UUID(as_uuid=True)` primary keys).

Per spec.md's "Documentación de soporte no se persiste", this model has no
column for the uploaded document bytes — only the outcome (`estado`,
`prima_mensual`, vigencia, `referencia_externa`) ever reach this table.

This is a pure persistence model — mapping to/from the
`PolizaArrendamiento` domain entity happens in
`seguro_arrendamiento/infrastructure/persistence/repository.py`, never
here.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class PolizaArrendamientoORM(Base):
    __tablename__ = "polizas_arrendamiento"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prima_mensual: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    vigencia_desde: Mapped[date | None] = mapped_column(Date(), nullable=True)
    vigencia_hasta: Mapped[date | None] = mapped_column(Date(), nullable=True)
    referencia_externa: Mapped[str | None] = mapped_column(String(255), nullable=True)
