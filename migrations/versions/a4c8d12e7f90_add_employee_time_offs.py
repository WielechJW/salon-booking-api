"""add employee time offs

Revision ID: a4c8d12e7f90
Revises: 5e1b7a9c2d04
Create Date: 2026-10-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4c8d12e7f90"
down_revision: Union[str, Sequence[str], None] = "5e1b7a9c2d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create employee time off periods."""
    op.create_table(
        "employee_time_offs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_employee_time_offs_end_after_start",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_employee_time_offs_employee_time_range",
        "employee_time_offs",
        ["employee_id", "start_at", "end_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop employee time off periods."""
    op.drop_index(
        "ix_employee_time_offs_employee_time_range",
        table_name="employee_time_offs",
    )
    op.drop_table("employee_time_offs")
