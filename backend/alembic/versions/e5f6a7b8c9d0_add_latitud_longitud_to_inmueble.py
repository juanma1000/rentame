"""add latitud/longitud to inmueble

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "inmueble", sa.Column("latitud", sa.Numeric(precision=9, scale=6), nullable=True)
    )
    op.add_column(
        "inmueble", sa.Column("longitud", sa.Numeric(precision=9, scale=6), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inmueble", "longitud")
    op.drop_column("inmueble", "latitud")
