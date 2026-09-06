"""create validaciones_identidad table, add identidad_verificada to usuario

Revision ID: a1b2c3d4e5f6
Revises: 88258bd709c5
Create Date: 2026-09-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "88258bd709c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuario",
        sa.Column(
            "identidad_verificada",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_table(
        "validaciones_identidad",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("cedula", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_externa", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("validaciones_identidad")
    op.drop_column("usuario", "identidad_verificada")
