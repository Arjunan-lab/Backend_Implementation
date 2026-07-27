"""create chat history table

Revision ID: e5f6a7b8c9d0
Revises: d4d5f6a7b8c9
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4d5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the table used to persist chatbot conversations."""
    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("prediction_history_id", sa.Integer(), nullable=True),
        sa.Column("user_message", sa.String(), nullable=False),
        sa.Column("assistant_response", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["prediction_history_id"], ["prediction_history.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_history_id"), "chat_history", ["id"], unique=False)
    op.create_index(op.f("ix_chat_history_user_id"), "chat_history", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_chat_history_prediction_history_id"),
        "chat_history",
        ["prediction_history_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the chatbot conversation table."""
    op.drop_index(op.f("ix_chat_history_prediction_history_id"), table_name="chat_history")
    op.drop_index(op.f("ix_chat_history_user_id"), table_name="chat_history")
    op.drop_index(op.f("ix_chat_history_id"), table_name="chat_history")
    op.drop_table("chat_history")
