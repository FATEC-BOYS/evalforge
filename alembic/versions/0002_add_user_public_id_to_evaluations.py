"""add user_public_id to evaluations

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evaluations",
        sa.Column(
            "user_public_id",
            sa.String(255),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_evaluations_user_public_id",
        "evaluations",
        ["user_public_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_evaluations_user_public_id", table_name="evaluations")
    op.drop_column("evaluations", "user_public_id")
