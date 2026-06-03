"""005_add_calendar_events

Revision ID: 005
Revises: 004
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", sa.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("all_day", sa.Boolean(), default=False, nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("recurrence_rule", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_calendar_events_account_id", "calendar_events", ["account_id"])
    op.create_index("ix_calendar_events_start_at", "calendar_events", ["start_at"])


def downgrade() -> None:
    op.drop_index("ix_calendar_events_start_at", table_name="calendar_events")
    op.drop_index("ix_calendar_events_account_id", table_name="calendar_events")
    op.drop_table("calendar_events")
