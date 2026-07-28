"""add_username_status_region_to_users

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-28 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add username column
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Add status column with default value 'active'
    op.add_column('users', sa.Column('status', sa.String(length=20), server_default='active', nullable=False))
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)

    # Add region column
    op.add_column('users', sa.Column('region', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_users_region'), 'users', ['region'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_region'), table_name='users')
    op.drop_column('users', 'region')

    op.drop_index(op.f('ix_users_status'), table_name='users')
    op.drop_column('users', 'status')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
