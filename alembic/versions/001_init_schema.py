"""init_schema

Revision ID: 001_init_schema
Revises:
Create Date: 2026-09-30 13:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_init_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "spaces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("space_type", sa.String(length=30), nullable=False, server_default="desk"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("has_projector", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_whiteboard", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_spaces_title"), "spaces", ["title"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("space_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_user_id"), "bookings", ["user_id"], unique=False)
    op.create_index(op.f("ix_bookings_space_id"), "bookings", ["space_id"], unique=False)
    op.create_index(op.f("ix_bookings_start_time"), "bookings", ["start_time"], unique=False)
    op.create_index(op.f("ix_bookings_end_time"), "bookings", ["end_time"], unique=False)
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_status"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_end_time"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_start_time"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_space_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_user_id"), table_name="bookings")
    op.drop_table("bookings")

    op.drop_index(op.f("ix_spaces_title"), table_name="spaces")
    op.drop_table("spaces")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
