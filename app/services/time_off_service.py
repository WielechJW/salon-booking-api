from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employee import EmployeeModel
from app.models.employee_time_off import EmployeeTimeOffModel
from app.services.calendar_service import (
    get_overlapping_appointments,
    get_overlapping_time_offs,
    lock_employee_calendar,
)
from app.services.errors import (
    DomainConflictError,
    DomainNotFoundError,
    DomainValidationError,
)
from app.timezone import as_utc


def normalize_time_range(
    *,
    start_at: datetime,
    end_at: datetime,
) -> tuple[datetime, datetime]:
    timestamps = (start_at, end_at)

    if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
        raise DomainValidationError(
            "Time off timestamps must include a timezone offset"
        )

    normalized_start = as_utc(start_at)
    normalized_end = as_utc(end_at)

    if normalized_start >= normalized_end:
        raise DomainValidationError("start_at must be before end_at")

    return normalized_start, normalized_end


def get_employee_or_raise(
    *,
    database_session: Session,
    employee_id: int,
) -> EmployeeModel:
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise DomainNotFoundError("Employee not found")

    return employee


def get_time_off_or_raise(
    *,
    database_session: Session,
    employee_id: int,
    time_off_id: int,
) -> EmployeeTimeOffModel:
    time_off = database_session.scalar(
        select(EmployeeTimeOffModel).where(
            EmployeeTimeOffModel.id == time_off_id,
            EmployeeTimeOffModel.employee_id == employee_id,
        )
    )

    if time_off is None:
        raise DomainNotFoundError("Time off not found")

    return time_off


def validate_time_off_conflicts(
    *,
    database_session: Session,
    employee_id: int,
    start_at: datetime,
    end_at: datetime,
    exclude_time_off_id: int | None = None,
) -> None:
    appointments = get_overlapping_appointments(
        database_session=database_session,
        employee_id=employee_id,
        start_at=start_at,
        end_at=end_at,
    )

    if appointments:
        raise DomainConflictError("Time off overlaps an existing appointment")

    time_offs = get_overlapping_time_offs(
        database_session=database_session,
        employee_id=employee_id,
        start_at=start_at,
        end_at=end_at,
        exclude_time_off_id=exclude_time_off_id,
    )

    if time_offs:
        raise DomainConflictError("Time off overlaps an existing time off")


def list_employee_time_offs(
    *,
    database_session: Session,
    employee_id: int,
) -> list[EmployeeTimeOffModel]:
    get_employee_or_raise(
        database_session=database_session,
        employee_id=employee_id,
    )
    query = (
        select(EmployeeTimeOffModel)
        .where(EmployeeTimeOffModel.employee_id == employee_id)
        .order_by(EmployeeTimeOffModel.start_at, EmployeeTimeOffModel.id)
    )
    return list(database_session.scalars(query).all())


def create_time_off(
    *,
    database_session: Session,
    employee_id: int,
    start_at: datetime,
    end_at: datetime,
    reason: str,
) -> EmployeeTimeOffModel:
    normalized_start, normalized_end = normalize_time_range(
        start_at=start_at,
        end_at=end_at,
    )
    get_employee_or_raise(
        database_session=database_session,
        employee_id=employee_id,
    )
    lock_employee_calendar(
        database_session=database_session,
        employee_id=employee_id,
    )
    validate_time_off_conflicts(
        database_session=database_session,
        employee_id=employee_id,
        start_at=normalized_start,
        end_at=normalized_end,
    )

    time_off = EmployeeTimeOffModel(
        employee_id=employee_id,
        start_at=normalized_start,
        end_at=normalized_end,
        reason=reason,
    )
    database_session.add(time_off)
    database_session.commit()
    database_session.refresh(time_off)
    return time_off


def update_time_off(
    *,
    database_session: Session,
    employee_id: int,
    time_off_id: int,
    start_at: datetime,
    end_at: datetime,
    reason: str,
) -> EmployeeTimeOffModel:
    normalized_start, normalized_end = normalize_time_range(
        start_at=start_at,
        end_at=end_at,
    )
    get_employee_or_raise(
        database_session=database_session,
        employee_id=employee_id,
    )
    lock_employee_calendar(
        database_session=database_session,
        employee_id=employee_id,
    )
    time_off = get_time_off_or_raise(
        database_session=database_session,
        employee_id=employee_id,
        time_off_id=time_off_id,
    )
    validate_time_off_conflicts(
        database_session=database_session,
        employee_id=employee_id,
        start_at=normalized_start,
        end_at=normalized_end,
        exclude_time_off_id=time_off_id,
    )

    time_off.start_at = normalized_start
    time_off.end_at = normalized_end
    time_off.reason = reason
    database_session.commit()
    database_session.refresh(time_off)
    return time_off


def delete_time_off(
    *,
    database_session: Session,
    employee_id: int,
    time_off_id: int,
) -> None:
    get_employee_or_raise(
        database_session=database_session,
        employee_id=employee_id,
    )
    lock_employee_calendar(
        database_session=database_session,
        employee_id=employee_id,
    )
    time_off = get_time_off_or_raise(
        database_session=database_session,
        employee_id=employee_id,
        time_off_id=time_off_id,
    )
    database_session.delete(time_off)
    database_session.commit()
