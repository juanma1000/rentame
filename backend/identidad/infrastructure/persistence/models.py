"""SQLAlchemy 2.0 async ORM model for the `identidad` domain.

Maps 1:1 to the `validaciones_identidad` table (task 4.3 of
`openspec/changes/validacion-identidad-inquilino/tasks.md`). Mirrors the
style already established by
`agencias/infrastructure/persistence/models.py` (SQLAlchemy 2.0
`Mapped`/`mapped_column`, `postgresql.UUID(as_uuid=True)` primary keys,
`server_default func.now()` timestamps).

Per spec.md's "Imágenes del documento no se persisten", this model has no
column for the document image bytes — only the outcome (`estado`), `cedula`
as text, `fecha` and `referencia_externa` ever reach this table.

This is a pure persistence model — mapping to/from the `ValidacionIdentidad`
domain entity happens in
`identidad/infrastructure/persistence/repository.py`, never here.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class ValidacionIdentidadORM(Base):
    __tablename__ = "validaciones_identidad"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    cedula: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_externa: Mapped[str | None] = mapped_column(String(255), nullable=True)
