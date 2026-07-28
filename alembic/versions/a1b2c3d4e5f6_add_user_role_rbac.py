"""add user role rbac

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-07-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "55377ae63dbc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column with default 'farmer' to users table."""
    op.add_column("users", sa.Column("role", sa.String(length=20), server_default="farmer", nullable=False))
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)


def downgrade() -> None:
    """Remove role column from users table."""
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "role")
