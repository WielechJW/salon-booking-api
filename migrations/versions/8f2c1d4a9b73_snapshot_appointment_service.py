"""snapshot appointment service data

Revision ID: 8f2c1d4a9b73
Revises: cf8d508ac5ac
Create Date: 2026-09-29 12:00:00.000000

"""

from datetime import timedelta
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f2c1d4a9b73"
down_revision: Union[str, Sequence[str], None] = "cf8d508ac5ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add and backfill immutable service data on appointments."""
    op.add_column(
        "appointments",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("end_at", sa.DateTime(), nullable=True),
    )

    appointments = sa.table(
        "appointments",
        sa.column("id", sa.Integer()),
        sa.column("service_id", sa.Integer()),
        sa.column("start_at", sa.DateTime()),
        sa.column("duration_minutes", sa.Integer()),
        sa.column("price", sa.Numeric(10, 2)),
        sa.column("end_at", sa.DateTime()),
    )
    services = sa.table(
        "services",
        sa.column("id", sa.Integer()),
        sa.column("duration_minutes", sa.Integer()),
        sa.column("price", sa.Numeric(10, 2)),
    )

    connection = op.get_bind()
    existing_appointments = (
        connection.execute(
            sa.select(
                appointments.c.id,
                appointments.c.start_at,
                services.c.duration_minutes,
                services.c.price,
            ).join(services, appointments.c.service_id == services.c.id)
        )
        .mappings()
        .all()
    )

    for appointment in existing_appointments:
        connection.execute(
            appointments.update()
            .where(appointments.c.id == appointment["id"])
            .values(
                duration_minutes=appointment["duration_minutes"],
                price=appointment["price"],
                end_at=appointment["start_at"]
                + timedelta(minutes=appointment["duration_minutes"]),
            )
        )

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column(
            "duration_minutes",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "end_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_appointments_duration_positive",
            "duration_minutes > 0",
        )
        batch_op.create_check_constraint(
            "ck_appointments_price_nonnegative",
            "price >= 0",
        )
        batch_op.create_check_constraint(
            "ck_appointments_end_after_start",
            "end_at > start_at",
        )
        batch_op.create_index(
            "ix_appointments_end_at",
            ["end_at"],
            unique=False,
        )


def downgrade() -> None:
    """Remove appointment service snapshots."""
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_index("ix_appointments_end_at")
        batch_op.drop_constraint(
            "ck_appointments_end_after_start",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_appointments_price_nonnegative",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_appointments_duration_positive",
            type_="check",
        )
        batch_op.drop_column("end_at")
        batch_op.drop_column("price")
        batch_op.drop_column("duration_minutes")
