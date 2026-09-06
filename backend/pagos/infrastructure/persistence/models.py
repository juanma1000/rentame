"""SQLAlchemy 2.0 async ORM model for the `pagos` domain.

Maps 1:1 to the `pagos` table (task 6.3 of
`openspec/changes/pago-mensual-renta/tasks.md`). Mirrors the style already
established by `firma_contrato/infrastructure/persistence/models.py`
(SQLAlchemy 2.0 `Mapped`/`mapped_column`, `postgresql.UUID(as_uuid=True)`
primary keys).

This is a pure persistence model — mapping to/from the `Pago` domain
entity happens in `pagos/infrastructure/persistence/repository.py`, never
here.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class PagoORM(Base):
    __tablename__ = "pagos"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    arrendamiento_activo_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("arrendamientos_activos.id"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_limite: Mapped[date] = mapped_column(Date(), nullable=False)
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referencia_externa: Mapped[str | None] = mapped_column(String(255), nullable=True)
