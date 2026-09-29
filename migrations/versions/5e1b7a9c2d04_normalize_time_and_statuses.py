"""normalize appointment time and statuses

Revision ID: 5e1b7a9c2d04
Revises: 8f2c1d4a9b73
Create Date: 2026-09-29 13:00:00.000000

"""

from datetime import timezone
from typing import Sequence, Union
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5e1b7a9c2d04"
down_revision: Union[str, Sequence[str], None] = "8f2c1d4a9b73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SALON_TIMEZONE = ZoneInfo("Europe/Warsaw")
UTC = timezone.utc


def _convert_sqlite_appointments(*, to_utc: bool) -> None:
    appointments = sa.table(
        "appointments",
        sa.column("id", sa.Integer()),
        sa.column("start_at", sa.DateTime()),
        sa.column("end_at", sa.DateTime()),
    )
    connection = op.get_bind()
    rows = (
        connection.execute(
            sa.select(
                appointments.c.id,
                appointments.c.start_at,
                appointments.c.end_at,
            )
        )
        .mappings()
        .all()
    )

    for appointment in rows:
        if to_utc:
            start_at = (
                appointment["start_at"]
                .replace(tzinfo=SALON_TIMEZONE)
                .astimezone(UTC)
                .replace(tzinfo=None)
            )
            end_at = (
                appointment["end_at"]
                .replace(tzinfo=SALON_TIMEZONE)
                .astimezone(UTC)
                .replace(tzinfo=None)
            )
        else:
            start_at = (
                appointment["start_at"]
                .replace(tzinfo=UTC)
                .astimezone(SALON_TIMEZONE)
                .replace(tzinfo=None)
            )
            end_at = (
                appointment["end_at"]
                .replace(tzinfo=UTC)
                .astimezone(SALON_TIMEZONE)
                .replace(tzinfo=None)
            )

        connection.execute(
            appointments.update()
            .where(appointments.c.id == appointment["id"])
            .values(start_at=start_at, end_at=end_at)
        )


def upgrade() -> None:
    """Store appointment timestamps as UTC and constrain their statuses."""
    dialect_name = op.get_bind().dialect.name

    if dialect_name == "postgresql":
        op.alter_column(
            "appointments",
            "start_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="start_at AT TIME ZONE 'Europe/Warsaw'",
        )
        op.alter_column(
            "appointments",
            "end_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="end_at AT TIME ZONE 'Europe/Warsaw'",
        )
        op.create_check_constraint(
            "ck_appointments_status",
            "appointments",
            "status IN ('pending', 'confirmed', 'cancelled', 'completed')",
        )
        return

    if dialect_name != "sqlite":
        raise RuntimeError(f"Unsupported database dialect: {dialect_name}")

    _convert_sqlite_appointments(to_utc=True)

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column(
            "start_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "end_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_appointments_status",
            "status IN ('pending', 'confirmed', 'cancelled', 'completed')",
        )


def downgrade() -> None:
    """Restore naive Europe/Warsaw appointment timestamps."""
    dialect_name = op.get_bind().dialect.name

    if dialect_name == "postgresql":
        op.drop_constraint(
            "ck_appointments_status",
            "appointments",
            type_="check",
        )
        op.alter_column(
            "appointments",
            "start_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            postgresql_using="start_at AT TIME ZONE 'Europe/Warsaw'",
        )
        op.alter_column(
            "appointments",
            "end_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            postgresql_using="end_at AT TIME ZONE 'Europe/Warsaw'",
        )
        return

    if dialect_name != "sqlite":
        raise RuntimeError(f"Unsupported database dialect: {dialect_name}")

    _convert_sqlite_appointments(to_utc=False)

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_constraint("ck_appointments_status", type_="check")
        batch_op.alter_column(
            "start_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "end_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
