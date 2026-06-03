"""003_model_alignment

Revision ID: 003
Revises: 002
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("recovery_codes", sa.JSON(), nullable=True))
    op.add_column("domains", sa.Column("dkim_private_key_encrypted", sa.Text(), nullable=True))
    op.add_column("stripe_events", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("stripe_events", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("stripe_events", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("stripe_events", "attempt_count", server_default=None)


def downgrade() -> None:
    op.drop_column("stripe_events", "locked_until")
    op.drop_column("stripe_events", "last_attempt_at")
    op.drop_column("stripe_events", "attempt_count")
    op.drop_column("domains", "dkim_private_key_encrypted")
    op.drop_column("accounts", "recovery_codes")
