"""Add user accounts and appointment/employee ownership.

Revision ID: b7f2a9c41d06
Revises: a4c8d12e7f90
"""

import sqlalchemy as sa
from alembic import op

revision = "b7f2a9c41d06"
down_revision = "a4c8d12e7f90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('CLIENT', 'EMPLOYEE', 'ADMIN')", name="ck_users_role"
        ),
    )
    with op.batch_alter_table("employees") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_employees_user_id", "users", ["user_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_unique_constraint("uq_employees_user_id", ["user_id"])

    with op.batch_alter_table("appointments") as batch:
        batch.add_column(sa.Column("client_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_appointments_client_id",
            "users",
            ["client_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_appointments_client_id", ["client_id"])


def downgrade() -> None:
    with op.batch_alter_table("appointments") as batch:
        batch.drop_index("ix_appointments_client_id")
        batch.drop_constraint("fk_appointments_client_id", type_="foreignkey")
        batch.drop_column("client_id")

    with op.batch_alter_table("employees") as batch:
        batch.drop_constraint("uq_employees_user_id", type_="unique")
        batch.drop_constraint("fk_employees_user_id", type_="foreignkey")
        batch.drop_column("user_id")

    op.drop_table("users")
