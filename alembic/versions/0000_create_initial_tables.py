"""create initial tables: users and evaluations

Revision ID: 0000
Revises:
Create Date: 2026-05-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.LargeBinary(16), primary_key=True, nullable=False),
        sa.Column("public_id", sa.String(36), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("tier", sa.String(10), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True, unique=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True, unique=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "evaluations",
        sa.Column("id", sa.LargeBinary(16), primary_key=True, nullable=False),
        sa.Column("public_id", sa.String(36), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("scores_json", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("verdict", sa.String(4), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
