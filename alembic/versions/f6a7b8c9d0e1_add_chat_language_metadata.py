"""add chat language metadata

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store detected and preferred languages with each chat conversation."""
    op.add_column("chat_history", sa.Column("question_language", sa.String(length=50), nullable=True))
    op.add_column("chat_history", sa.Column("preferred_language", sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove chat language metadata."""
    op.drop_column("chat_history", "preferred_language")
    op.drop_column("chat_history", "question_language")
