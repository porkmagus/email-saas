"""002_abuse_limits_stripe_events

Revision ID: 002
Revises: 001
Create Date: 2026-06-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # stripe_events
    op.create_table(
        "stripe_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("stripe_event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("processing_status", sa.Enum("received", "processing", "completed", "failed", "retrying", name="stripe_event_status"), nullable=False, server_default="received"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_stripe_events_stripe_event_id", "stripe_events", ["stripe_event_id"], unique=True)
    op.create_index("ix_stripe_events_event_type", "stripe_events", ["event_type"])
    op.create_index("ix_stripe_events_account_id", "stripe_events", ["account_id"])

    # send_events
    op.create_table(
        "send_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient_domain", sa.String(255), nullable=True),
        sa.Column("recipient_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.Enum("sent", "bounced", "complained", "deferred", "rejected", name="send_event_status"), nullable=False, server_default="sent"),
        sa.Column("message_size", sa.Integer(), nullable=True),
        sa.Column("has_attachments", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_send_events_account_id", "send_events", ["account_id"])
    op.create_index("ix_send_events_domain_id", "send_events", ["domain_id"])
    op.create_index("ix_send_events_mailbox_id", "send_events", ["mailbox_id"])
    op.create_index("ix_send_events_created_at", "send_events", ["created_at"])

    # abuse_scores
    op.create_table(
        "abuse_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("bounce_rate", sa.Float(), default=0.0, nullable=False),
        sa.Column("complaint_rate", sa.Float(), default=0.0, nullable=False),
        sa.Column("failed_auth_rate", sa.Float(), default=0.0, nullable=False),
        sa.Column("send_spike_score", sa.Float(), default=0.0, nullable=False),
        sa.Column("suspicious_recipient_score", sa.Float(), default=0.0, nullable=False),
        sa.Column("blacklist_count", sa.Integer(), default=0, nullable=False),
        sa.Column("total_score", sa.Float(), default=0.0, nullable=False),
        sa.Column("status", sa.Enum("green", "yellow", "orange", "red", name="abuse_score_status"), nullable=False, server_default="green"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    op.create_index("ix_abuse_scores_account_id", "abuse_scores", ["account_id"], unique=True)

    # outbound_limits
    op.create_table(
        "outbound_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id", ondelete="CASCADE"), nullable=True),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("period", sa.Enum("hourly", "daily", "monthly", name="outbound_limit_period"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("emails_sent", sa.Integer(), default=0, nullable=False),
        sa.Column("emails_allowed", sa.Integer(), default=0, nullable=False),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_outbound_limits_account_id", "outbound_limits", ["account_id"])
    op.create_index("ix_outbound_limits_domain_id", "outbound_limits", ["domain_id"])
    op.create_index("ix_outbound_limits_mailbox_id", "outbound_limits", ["mailbox_id"])
    op.create_index("ix_outbound_limits_period_start", "outbound_limits", ["period_start"])

    # maintenance_windows
    op.create_table(
        "maintenance_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), default="scheduled", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )
    op.create_index("ix_maintenance_windows_start_at", "maintenance_windows", ["start_at"])


def downgrade() -> None:
    op.drop_table("maintenance_windows")
    op.drop_table("outbound_limits")
    op.drop_table("abuse_scores")
    op.drop_table("send_events")
    op.drop_table("stripe_events")
    op.execute("DROP TYPE IF EXISTS stripe_event_status")
    op.execute("DROP TYPE IF EXISTS send_event_status")
    op.execute("DROP TYPE IF EXISTS abuse_score_status")
    op.execute("DROP TYPE IF EXISTS outbound_limit_period")
