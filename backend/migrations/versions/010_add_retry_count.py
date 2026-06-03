"""010_add_retry_count

Revision ID: 010
Revises: 009
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("import_jobs", sa.Column("retry_count", sa.Integer(), default=0, nullable=False))
    op.add_column("export_jobs", sa.Column("retry_count", sa.Integer(), default=0, nullable=False))


def downgrade() -> None:
    op.drop_column("export_jobs", "retry_count")
    op.drop_column("import_jobs", "retry_count")
