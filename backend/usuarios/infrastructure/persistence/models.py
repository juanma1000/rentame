"""Minimal `usuario` persistence model.

This is intentionally NOT the full `usuarios` domain from
`docs/architecture/architecture.md` (no password hash, name, phone, active
flag, etc.) — registration/login is out of scope for every HU in the current
backlog (HU-001 to HU-006). This model exists only so `inmuebles.propietario_id`
has a real FK target and so JWTs issued in tests reference a real row.

A future auth HU will own the full `usuario` entity/domain/use cases; at that
point this ORM model should move under a proper `usuarios/domain/` +
`usuarios/application/` split instead of living infrastructure-only.

`agencia_id` (task 5.2 of `openspec/changes/hu-007/tasks.md`) is the
membership pointer for agente users, per `design.md` decisión 2: a nullable
FK to `agencia.id` instead of a separate join table (cardinalidad 1 agente :
1 agencia). Only meaningful when `rol="agente"`; the `agencias` domain's
`UsuarioAgenciaRepositoryPort` (`agencias/domain/ports.py`) is the sole way
the application layer reads/writes it.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class UsuarioORM(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    agencia_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("agencia.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
