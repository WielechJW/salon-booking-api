from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.employee_time_off import EmployeeTimeOffModel
from app.timezone import as_utc


def overlap_conditions(
    first_start: Any,
    first_end: Any,
    second_start: Any,
    second_end: Any,
) -> tuple[Any, Any]:
    return first_start < second_end, first_end > second_start


def time_ranges_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return all(
        overlap_conditions(
            as_utc(first_start),
            as_utc(first_end),
            as_utc(second_start),
            as_utc(second_end),
        )
    )


def lock_employee_calendar(
    *,
    database_session: Session,
    employee_id: int,
) -> None:
    database_session.execute(
        select(EmployeeModel.id)
        .where(EmployeeModel.id == employee_id)
        .with_for_update()
    ).scalar_one()


def get_overlapping_appointments(
    *,
    database_session: Session,
    employee_id: int,
    start_at: datetime,
    end_at: datetime,
) -> Sequence[AppointmentModel]:
    query = select(AppointmentModel).where(
        AppointmentModel.employee_id == employee_id,
        AppointmentModel.status != "cancelled",
        *overlap_conditions(
            AppointmentModel.start_at,
            AppointmentModel.end_at,
            start_at,
            end_at,
        ),
    )
    return database_session.scalars(query).all()


def get_overlapping_time_offs(
    *,
    database_session: Session,
    employee_id: int,
    start_at: datetime,
    end_at: datetime,
    exclude_time_off_id: int | None = None,
) -> Sequence[EmployeeTimeOffModel]:
    query = select(EmployeeTimeOffModel).where(
        EmployeeTimeOffModel.employee_id == employee_id,
        *overlap_conditions(
            EmployeeTimeOffModel.start_at,
            EmployeeTimeOffModel.end_at,
            start_at,
            end_at,
        ),
    )

    if exclude_time_off_id is not None:
        query = query.where(EmployeeTimeOffModel.id != exclude_time_off_id)

    return database_session.scalars(query).all()
