"""004_add_all_email_saas_models

Revision ID: 004
Revises: 003
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add catch_all_target_mailbox_id to domains
    op.add_column("domains", sa.Column("catch_all_target_mailbox_id", sa.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_domains_catch_all_target_mailbox_id",
        "domains",
        "mailboxes",
        ["catch_all_target_mailbox_id"],
        ["id"],
    )

    # 2. aliases table
    op.create_table(
        "aliases",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("destination_local_part", sa.String(), nullable=False),
        sa.Column("destination_domain_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("domain_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["destination_domain_id"], ["domains.id"], name="fk_aliases_destination_domain_id"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], name="fk_aliases_domain_id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_aliases_account_id"),
    )
    op.create_index("ix_aliases_domain_id", "aliases", ["domain_id"])
    op.create_index("ix_aliases_destination_domain_id", "aliases", ["destination_domain_id"])
    op.create_index("ix_aliases_account_id", "aliases", ["account_id"])

    # 3. email_rules table
    op.create_table(
        "email_rules",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_email_rules_account_id"),
    )
    op.create_index("ix_email_rules_account_id", "email_rules", ["account_id"])

    # 4. email_rule_conditions table
    op.create_table(
        "email_rule_conditions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("rule_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["email_rules.id"], name="fk_email_rule_conditions_rule_id"),
    )
    op.create_index("ix_email_rule_conditions_rule_id", "email_rule_conditions", ["rule_id"])

    # 5. email_rule_actions table
    op.create_table(
        "email_rule_actions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("target_mailbox_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("rule_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["target_mailbox_id"], ["mailboxes.id"], name="fk_email_rule_actions_target_mailbox_id"),
        sa.ForeignKeyConstraint(["rule_id"], ["email_rules.id"], name="fk_email_rule_actions_rule_id"),
    )
    op.create_index("ix_email_rule_actions_rule_id", "email_rule_actions", ["rule_id"])
    op.create_index("ix_email_rule_actions_target_mailbox_id", "email_rule_actions", ["target_mailbox_id"])

    # 6. vacation_response table
    op.create_table(
        "vacation_response",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("only_contacts", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("only_aliases", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_vacation_response_account_id"),
        sa.UniqueConstraint("account_id", name="uq_vacation_response_account_id"),
    )
    op.create_index("ix_vacation_response_account_id", "vacation_response", ["account_id"], unique=True)

    # 7. blocked_senders table
    op.create_table(
        "blocked_senders",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email_or_domain", sa.String(), nullable=False),
        sa.Column("is_domain", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_blocked_senders_account_id"),
    )
    op.create_index("ix_blocked_senders_account_id", "blocked_senders", ["account_id"])
    op.create_index("ix_blocked_senders_email_or_domain", "blocked_senders", ["email_or_domain"])

    # 8. contacts table
    op.create_table(
        "contacts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_vip", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_contacts_account_id"),
    )
    op.create_index("ix_contacts_account_id", "contacts", ["account_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])

    # 9. contact_groups table
    op.create_table(
        "contact_groups",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_contact_groups_account_id"),
    )
    op.create_index("ix_contact_groups_account_id", "contact_groups", ["account_id"])

    # 10. contact_group_members table
    op.create_table(
        "contact_group_members",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("contact_group_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["contact_group_id"], ["contact_groups.id"], name="fk_contact_group_members_group_id"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], name="fk_contact_group_members_contact_id"),
    )
    op.create_index("ix_contact_group_members_group_id", "contact_group_members", ["contact_group_id"])
    op.create_index("ix_contact_group_members_contact_id", "contact_group_members", ["contact_id"])

    # 11. passkeys table
    op.create_table(
        "passkeys",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("credential_id", sa.String(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("device_name", sa.String(), nullable=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_passkeys_account_id"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], name="fk_passkeys_mailbox_id"),
    )
    op.create_index("ix_passkeys_account_id", "passkeys", ["account_id"])
    op.create_index("ix_passkeys_mailbox_id", "passkeys", ["mailbox_id"])
    op.create_index("ix_passkeys_credential_id", "passkeys", ["credential_id"], unique=True)

    # 12. app_passwords table
    op.create_table(
        "app_passwords",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_app_passwords_account_id"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], name="fk_app_passwords_mailbox_id"),
    )
    op.create_index("ix_app_passwords_account_id", "app_passwords", ["account_id"])
    op.create_index("ix_app_passwords_mailbox_id", "app_passwords", ["mailbox_id"])

    # 13. login_logs table
    op.create_table(
        "login_logs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_login_logs_account_id"),
    )
    op.create_index("ix_login_logs_account_id", "login_logs", ["account_id"])
    op.create_index("ix_login_logs_created_at", "login_logs", ["created_at"])

    # 14. sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("last_active", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_sessions_account_id"),
    )
    op.create_index("ix_sessions_account_id", "sessions", ["account_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    # 15. notes table
    op.create_table(
        "notes",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_notes_account_id"),
    )
    op.create_index("ix_notes_account_id", "notes", ["account_id"])

    # 16. files table
    op.create_table(
        "files",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("folder", sa.String(), server_default="inbox", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("account_id", sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_files_account_id"),
    )
    op.create_index("ix_files_account_id", "files", ["account_id"])


def downgrade() -> None:
    op.drop_table("files")
    op.drop_table("notes")
    op.drop_table("sessions")
    op.drop_table("login_logs")
    op.drop_table("app_passwords")
    op.drop_table("passkeys")
    op.drop_table("contact_group_members")
    op.drop_table("contact_groups")
    op.drop_table("contacts")
    op.drop_table("blocked_senders")
    op.drop_table("vacation_response")
    op.drop_table("email_rule_actions")
    op.drop_table("email_rule_conditions")
    op.drop_table("email_rules")
    op.drop_table("aliases")
    op.drop_constraint("fk_domains_catch_all_target_mailbox_id", "domains", type_="foreignkey")
    op.drop_column("domains", "catch_all_target_mailbox_id")
