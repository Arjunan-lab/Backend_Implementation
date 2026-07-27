"""normalize language storage and tracking fields

Revision ID: d4d5f6a7b8c9
Revises: 436d531da2f1
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4d5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '436d531da2f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('language_name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_languages_id'), 'languages', ['id'], unique=False)
    op.create_index(op.f('ix_languages_language_name'), 'languages', ['language_name'], unique=True)

    op.execute(sa.text("""
        INSERT INTO languages (language_name)
        VALUES ('English'), ('Telugu'), ('Hindi'), ('Tamil')
        ON CONFLICT (language_name) DO NOTHING
    """))

    op.add_column('users', sa.Column('language_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_logout_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_users_language_id'), 'users', ['language_id'], unique=False)

    op.execute(sa.text("""
        UPDATE users
        SET language_id = (
            SELECT l.id
            FROM languages l
            WHERE l.language_name = users.preferred_language
        )
    """))

    op.create_foreign_key('fk_users_language_id_languages', 'users', 'languages', ['language_id'], ['id'])
    op.drop_column('users', 'preferred_language')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users', sa.Column('preferred_language', sa.String(length=50), nullable=True))
    op.execute(sa.text("""
        UPDATE users
        SET preferred_language = (
            SELECT l.language_name
            FROM languages l
            WHERE l.id = users.language_id
        )
    """))
    op.drop_constraint('fk_users_language_id_languages', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_language_id'), table_name='users')
    op.drop_column('users', 'last_logout_at')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'language_id')
    op.drop_index(op.f('ix_languages_language_name'), table_name='languages')
    op.drop_index(op.f('ix_languages_id'), table_name='languages')
    op.drop_table('languages')
