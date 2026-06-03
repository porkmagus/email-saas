"""009_add_webmail_tokens

Revision ID: 009
Revises: 008
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webmail_tokens",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", sa.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_webmail_tokens_account_id", "webmail_tokens", ["account_id"])
    op.create_index("ix_webmail_tokens_token", "webmail_tokens", ["token"], unique=True)
    op.create_index("ix_webmail_tokens_expires_at", "webmail_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_webmail_tokens_expires_at", table_name="webmail_tokens")
    op.drop_index("ix_webmail_tokens_token", table_name="webmail_tokens")
    op.drop_index("ix_webmail_tokens_account_id", table_name="webmail_tokens")
    op.drop_table("webmail_tokens")
