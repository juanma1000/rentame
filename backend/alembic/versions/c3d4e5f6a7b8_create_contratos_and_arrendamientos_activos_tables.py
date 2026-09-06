"""create contratos and arrendamientos_activos tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-06 00:00:01.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "contratos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("poliza_id", sa.UUID(), nullable=False),
        sa.Column("inmueble_id", sa.UUID(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("documento_referencia", sa.String(), nullable=False),
        sa.Column("referencia_externa", sa.String(length=255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["poliza_id"], ["polizas_arrendamiento.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "arrendamientos_activos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("poliza_id", sa.UUID(), nullable=False),
        sa.Column("contrato_id", sa.UUID(), nullable=False),
        sa.Column("inmueble_id", sa.UUID(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["poliza_id"], ["polizas_arrendamiento.id"]),
        sa.ForeignKeyConstraint(["contrato_id"], ["contratos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contrato_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("arrendamientos_activos")
    op.drop_table("contratos")
