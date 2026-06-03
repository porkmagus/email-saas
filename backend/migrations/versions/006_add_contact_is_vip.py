"""006_add_contact_is_vip

Revision ID: 006
Revises: 005
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_vip column to contacts if it doesn't already exist (e.g. from migration 004).
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("contacts")]
    if "is_vip" not in columns:
        op.add_column(
            "contacts",
            sa.Column("is_vip", sa.Boolean(), server_default="false", nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("contacts")]
    if "is_vip" in columns:
        op.drop_column("contacts", "is_vip")
