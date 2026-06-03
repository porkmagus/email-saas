"""007_add_import_and_export_jobs

Revision ID: 007
Revises: 006
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", sa.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("server", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), default=993, nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("tls", sa.Boolean(), default=True, nullable=False),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("messages_imported", sa.Integer(), default=0, nullable=False),
        sa.Column("errors", sa.Integer(), default=0, nullable=False),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_import_jobs_account_id", "import_jobs", ["account_id"])

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", sa.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_export_jobs_account_id", "export_jobs", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_export_jobs_account_id", table_name="export_jobs")
    op.drop_table("export_jobs")
    op.drop_index("ix_import_jobs_account_id", table_name="import_jobs")
    op.drop_table("import_jobs")
