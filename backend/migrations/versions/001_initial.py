"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-06-03 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("active", "suspended", "cancelled", "pending", name="account_status"), nullable=False),
        sa.Column("plan", sa.Enum("starter", "pro", "enterprise", name="plan_tier"), nullable=False),
        sa.Column("role", sa.Enum("customer", "admin", "superadmin", name="account_role"), nullable=False),
        sa.Column("totp_secret", sa.String(255), nullable=True),
        sa.Column("totp_enabled", sa.Boolean, default=False, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_accounts_email", "accounts", ["email"], unique=True)
    op.create_index("ix_accounts_stripe_customer_id", "accounts", ["stripe_customer_id"])

    op.create_table(
        "domains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(255), unique=True, nullable=False),
        sa.Column("verified", sa.Boolean, default=False, nullable=False),
        sa.Column("mx_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("spf_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("dkim_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("dkim_selector", sa.String(255), nullable=True),
        sa.Column("mx_record", sa.String(255), nullable=True),
        sa.Column("spf_record", sa.Text, nullable=True),
        sa.Column("dkim_record", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_domains_account_id", "domains", ["account_id"])
    op.create_index("ix_domains_domain", "domains", ["domain"], unique=True)

    op.create_table(
        "mailboxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id", ondelete="CASCADE"), nullable=False),
        sa.Column("local_part", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("quota_bytes", sa.Integer, default=1073741824, nullable=False),
        sa.Column("status", sa.Enum("active", "suspended", "cancelled", "pending", name="mailbox_status"), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mailboxes_account_id", "mailboxes", ["account_id"])
    op.create_index("ix_mailboxes_domain_id", "mailboxes", ["domain_id"])
    op.create_index("ix_mailboxes_local_part_domain_id", "mailboxes", ["local_part", "domain_id"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), unique=True, nullable=False),
        sa.Column("status", sa.Enum("active", "past_due", "cancelled", "trialing", "unpaid", name="subscription_status"), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean, default=False, nullable=False),
        sa.Column("plan", sa.Enum("starter", "pro", "enterprise", name="subscription_plan_tier"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_account_id", "subscriptions", ["account_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"], unique=True)

    op.create_table(
        "provisioning_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("provision_account", "add_domain", "add_mailbox", "delete_mailbox", "suspend_account", "delete_account", name="job_type"), nullable=False),
        sa.Column("payload", sa.JSON, default=dict, nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "completed", "failed", "retrying", name="job_status"), nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_provisioning_jobs_account_id", "provisioning_jobs", ["account_id"])
    op.create_index("ix_provisioning_jobs_status", "provisioning_jobs", ["status"])

    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.Enum("open", "waiting_customer", "waiting_staff", "resolved", "closed", name="ticket_status"), nullable=False),
        sa.Column("priority", sa.Enum("low", "normal", "high", "critical", name="ticket_priority"), nullable=False),
        sa.Column("category", sa.Enum("billing", "setup", "delivery", "account", "other", name="ticket_category"), nullable=False),
        sa.Column("assigned_to", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tickets_account_id", "tickets", ["account_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_priority", "tickets", ["priority"])
    op.create_index("ix_tickets_assigned_to", "tickets", ["assigned_to"])

    op.create_table(
        "ticket_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("author_email", sa.String(255), nullable=True),
        sa.Column("is_internal", sa.Boolean, default=False, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ticket_comments_ticket_id", "ticket_comments", ["ticket_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("hashed_secret", sa.Text, nullable=False),
        sa.Column("permissions", sa.JSON, default=list, nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_account_id", "api_keys", ["account_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["prefix"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_type", sa.Enum("user", "admin", "system", "impersonation", name="actor_type"), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(255), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("meta_data", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_account_id", "audit_log", ["account_id"])
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_resource_type_resource_id", "audit_log", ["resource_type", "resource_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "suppressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_suppressions_email", "suppressions", ["email"], unique=True)
    op.create_index("ix_suppressions_domain", "suppressions", ["domain"])

    op.create_table(
        "metering_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Enum("emails_sent", "storage_bytes", "bandwidth_bytes", name="metering_event_type"), nullable=False),
        sa.Column("quantity", sa.Integer, default=0, nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_metering_events_account_id", "metering_events", ["account_id"])
    op.create_index("ix_metering_events_event_type", "metering_events", ["event_type"])
    op.create_index("ix_metering_events_period_start", "metering_events", ["period_start"])


def downgrade() -> None:
    op.drop_table("metering_events")
    op.drop_table("suppressions")
    op.drop_table("audit_log")
    op.drop_table("api_keys")
    op.drop_table("ticket_comments")
    op.drop_table("tickets")
    op.drop_table("provisioning_jobs")
    op.drop_table("subscriptions")
    op.drop_table("mailboxes")
    op.drop_table("domains")
    op.drop_table("accounts")
    op.execute("DROP TYPE IF EXISTS metering_event_type")
    op.execute("DROP TYPE IF EXISTS actor_type")
    op.execute("DROP TYPE IF EXISTS ticket_status")
    op.execute("DROP TYPE IF EXISTS ticket_priority")
    op.execute("DROP TYPE IF EXISTS ticket_category")
    op.execute("DROP TYPE IF EXISTS job_type")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS subscription_plan_tier")
    op.execute("DROP TYPE IF EXISTS mailbox_status")
    op.execute("DROP TYPE IF EXISTS account_status")
    op.execute("DROP TYPE IF EXISTS plan_tier")
    op.execute("DROP TYPE IF EXISTS account_role")
