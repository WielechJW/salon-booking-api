from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.employee_time_off import EmployeeTimeOffModel
from app.models.schedule import ScheduleModel
from app.models.service import ServiceModel
from app.services.booking_service import get_bookable_service
from app.services.calendar_service import (
    get_overlapping_appointments,
    get_overlapping_time_offs,
    overlap_conditions,
    time_ranges_overlap,
)
from app.services.errors import DomainNotFoundError, DomainValidationError
from app.timezone import as_utc, get_salon_timezone, utc_now

SLOT_STEP = timedelta(minutes=15)


@dataclass(frozen=True)
class Availability:
    employee_id: int
    service_id: int
    date: date
    available_slots: tuple[time, ...]


@dataclass(frozen=True)
class ServiceAvailabilitySlot:
    employee_id: int
    employee_name: str
    start_at: datetime
    end_at: datetime


def _work_bounds(
    target_date: date, schedule: ScheduleModel
) -> tuple[datetime, datetime]:
    salon_timezone = get_salon_timezone()
    try:
        return (
            as_utc(
                datetime.combine(
                    target_date, schedule.start_time, tzinfo=salon_timezone
                )
            ),
            as_utc(
                datetime.combine(target_date, schedule.end_time, tzinfo=salon_timezone)
            ),
        )
    except OverflowError as error:
        raise DomainValidationError(
            "Working hours cannot be represented in UTC"
        ) from error


def _slot_starts(
    *,
    work_start: datetime,
    work_end: datetime,
    service_duration: timedelta,
    unavailable_periods: Sequence[tuple[datetime, datetime]],
    current_time: datetime,
) -> tuple[datetime, ...]:
    slots = []
    slot_start = work_start
    while slot_start + service_duration <= work_end:
        slot_end = slot_start + service_duration
        if slot_start >= current_time and not any(
            time_ranges_overlap(slot_start, slot_end, start_at, end_at)
            for start_at, end_at in unavailable_periods
        ):
            slots.append(slot_start)
        slot_start += SLOT_STEP
    return tuple(slots)


def get_employee_availability(
    *,
    database_session: Session,
    employee_id: int,
    service_id: int,
    target_date: date,
    current_time: datetime | None = None,
) -> Availability:
    selected_service = get_bookable_service(
        database_session=database_session,
        employee_id=employee_id,
        service_id=service_id,
    )
    salon_timezone = get_salon_timezone()
    now = as_utc(current_time) if current_time is not None else utc_now()

    if target_date < now.astimezone(salon_timezone).date():
        return Availability(
            employee_id=employee_id,
            service_id=service_id,
            date=target_date,
            available_slots=(),
        )

    work_schedule = database_session.scalar(
        select(ScheduleModel).where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == target_date.weekday(),
        )
    )

    if work_schedule is None:
        return Availability(
            employee_id=employee_id,
            service_id=service_id,
            date=target_date,
            available_slots=(),
        )

    work_start, work_end = _work_bounds(target_date, work_schedule)
    appointments = get_overlapping_appointments(
        database_session=database_session,
        employee_id=employee_id,
        start_at=work_start,
        end_at=work_end,
    )
    time_offs = get_overlapping_time_offs(
        database_session=database_session,
        employee_id=employee_id,
        start_at=work_start,
        end_at=work_end,
    )

    service_duration = timedelta(minutes=selected_service.duration_minutes)
    starts = _slot_starts(
        work_start=work_start,
        work_end=work_end,
        service_duration=service_duration,
        unavailable_periods=[
            (period.start_at, period.end_at) for period in (*appointments, *time_offs)
        ],
        current_time=now,
    )

    return Availability(
        employee_id=employee_id,
        service_id=service_id,
        date=target_date,
        available_slots=tuple(
            start.astimezone(salon_timezone).time().replace(tzinfo=None)
            for start in starts
        ),
    )


def get_service_availability(
    *,
    database_session: Session,
    service_id: int,
    target_date: date,
    current_time: datetime | None = None,
) -> list[ServiceAvailabilitySlot]:
    selected_service = database_session.get(ServiceModel, service_id)
    if selected_service is None:
        raise DomainNotFoundError("Service not found")
    now = as_utc(current_time) if current_time is not None else utc_now()
    if target_date < now.astimezone(get_salon_timezone()).date():
        return []

    employees_and_schedules = database_session.execute(
        select(EmployeeModel, ScheduleModel)
        .join(
            EmployeeServiceModel, EmployeeServiceModel.employee_id == EmployeeModel.id
        )
        .join(ScheduleModel, ScheduleModel.employee_id == EmployeeModel.id)
        .where(
            EmployeeServiceModel.service_id == service_id,
            ScheduleModel.day_of_week == target_date.weekday(),
        )
    ).all()
    if not employees_and_schedules:
        return []

    shifts = [
        (employee, *_work_bounds(target_date, schedule))
        for employee, schedule in employees_and_schedules
    ]
    employee_ids = [employee.id for employee, _, _ in shifts]
    earliest_start = min(start for _, start, _ in shifts)
    latest_end = max(end for _, _, end in shifts)
    appointments = database_session.scalars(
        select(AppointmentModel).where(
            AppointmentModel.employee_id.in_(employee_ids),
            AppointmentModel.status != "cancelled",
            *overlap_conditions(
                AppointmentModel.start_at,
                AppointmentModel.end_at,
                earliest_start,
                latest_end,
            ),
        )
    ).all()
    time_offs = database_session.scalars(
        select(EmployeeTimeOffModel).where(
            EmployeeTimeOffModel.employee_id.in_(employee_ids),
            *overlap_conditions(
                EmployeeTimeOffModel.start_at,
                EmployeeTimeOffModel.end_at,
                earliest_start,
                latest_end,
            ),
        )
    ).all()
    busy_by_employee: dict[int, list[tuple[datetime, datetime]]] = defaultdict(list)
    for period in (*appointments, *time_offs):
        busy_by_employee[period.employee_id].append((period.start_at, period.end_at))

    duration = timedelta(minutes=selected_service.duration_minutes)
    slots = [
        ServiceAvailabilitySlot(
            employee_id=employee.id,
            employee_name=employee.name,
            start_at=start,
            end_at=start + duration,
        )
        for employee, work_start, work_end in shifts
        for start in _slot_starts(
            work_start=work_start,
            work_end=work_end,
            service_duration=duration,
            unavailable_periods=busy_by_employee[employee.id],
            current_time=now,
        )
    ]
    return sorted(slots, key=lambda slot: (slot.start_at, slot.employee_id))
