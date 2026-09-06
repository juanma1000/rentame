"""create pagos table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-06 00:00:02.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pagos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("arrendamiento_activo_id", sa.UUID(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fecha_limite", sa.Date(), nullable=False),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referencia_externa", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["arrendamiento_activo_id"], ["arrendamientos_activos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("pagos")
