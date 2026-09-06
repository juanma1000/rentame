"""`usuario` persistence model.

`password_hash` and `nombre` were added in HU-008 (registro/login real) as
`nullable=True` per `openspec/changes/hu-008/design.md` decisión 6, to avoid
breaking rows inserted manually in earlier development sessions (HU-001 to
HU-007) that predate this column. New rows created by `registrar_usuario`
always populate both.

`agencia_id` (task 5.2 of `openspec/changes/hu-007/tasks.md`) is the
membership pointer for agente users, per `design.md` decisión 2: a nullable
FK to `agencia.id` instead of a separate join table (cardinalidad 1 agente :
1 agencia). Only meaningful when `rol="agente"`; the `agencias` domain's
`UsuarioAgenciaRepositoryPort` (`agencias/domain/ports.py`) is the sole way
the application layer reads/writes it.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class UsuarioORM(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    agencia_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("agencia.id"), nullable=True
    )
    # Added by `openspec/changes/validacion-identidad-inquilino` (task 4.4):
    # `True` once `identidad`'s `iniciar_validacion_identidad` use case
    # registers an approved `ValidacionIdentidad` for this account.
    identidad_verificada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
