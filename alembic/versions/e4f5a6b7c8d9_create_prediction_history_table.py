"""create prediction history table

Revision ID: e4f5a6b7c8d9
Revises: d4d5f6a7b8c9
Create Date: 2026-07-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d4d5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create prediction history table."""
    op.create_table(
        "prediction_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("soil_image_path", sa.String(length=500), nullable=False),
        sa.Column("soil_type", sa.String(length=100), nullable=False),
        sa.Column("soil_confidence", sa.Float(), nullable=True),
        sa.Column("nitrogen", sa.Float(), nullable=False),
        sa.Column("phosphorus", sa.Float(), nullable=False),
        sa.Column("potassium", sa.Float(), nullable=False),
        sa.Column("ph", sa.Float(), nullable=False),
        sa.Column("organic_carbon", sa.Float(), nullable=False),
        sa.Column("electrical_conductivity", sa.Float(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("soil_health", sa.String(length=100), nullable=False),
        sa.Column("soil_health_score", sa.Float(), nullable=False),
        sa.Column("soil_fertility_status", sa.String(length=100), nullable=False),
        sa.Column("nutrient_deficiencies", sa.JSON(), nullable=False),
        sa.Column("recommended_crops", sa.JSON(), nullable=False),
        sa.Column("recommended_fertilizers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prediction_history_id"), "prediction_history", ["id"], unique=False)
    op.create_index(op.f("ix_prediction_history_user_id"), "prediction_history", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop prediction history table."""
    op.drop_index(op.f("ix_prediction_history_user_id"), table_name="prediction_history")
    op.drop_index(op.f("ix_prediction_history_id"), table_name="prediction_history")
    op.drop_table("prediction_history")
