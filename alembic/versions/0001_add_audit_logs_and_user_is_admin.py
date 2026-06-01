"""add audit_logs table and users.is_admin column

Revision ID: 0001
Revises:
Create Date: 2026-05-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BINARY(16), primary_key=True, nullable=False),
        sa.Column("public_id", sa.String(36), unique=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("user_public_id", sa.String(255), nullable=False),
        sa.Column("request_id", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("security_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_audit_logs_user_public_id",
        "audit_logs",
        ["user_public_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user_public_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_column("users", "is_admin")
