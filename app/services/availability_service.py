from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schedule import ScheduleModel
from app.services.booking_service import get_bookable_service
from app.services.calendar_service import (
    get_overlapping_appointments,
    get_overlapping_time_offs,
    time_ranges_overlap,
)
from app.timezone import as_utc, get_salon_timezone, utc_now

SLOT_STEP = timedelta(minutes=15)


@dataclass(frozen=True)
class Availability:
    employee_id: int
    service_id: int
    date: date
    available_slots: tuple[time, ...]


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

    local_work_start = datetime.combine(
        target_date,
        work_schedule.start_time,
        tzinfo=salon_timezone,
    )
    local_work_end = datetime.combine(
        target_date,
        work_schedule.end_time,
        tzinfo=salon_timezone,
    )
    work_start = as_utc(local_work_start)
    work_end = as_utc(local_work_end)
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
    available_slots = []
    slot_start = work_start

    while slot_start + service_duration <= work_end:
        if slot_start < now:
            slot_start += SLOT_STEP
            continue

        slot_end = slot_start + service_duration
        is_unavailable = any(
            time_ranges_overlap(
                slot_start,
                slot_end,
                unavailable_period.start_at,
                unavailable_period.end_at,
            )
            for unavailable_period in (*appointments, *time_offs)
        )

        if not is_unavailable:
            available_slots.append(
                slot_start.astimezone(salon_timezone).time().replace(tzinfo=None)
            )

        slot_start += SLOT_STEP

    return Availability(
        employee_id=employee_id,
        service_id=service_id,
        date=target_date,
        available_slots=tuple(available_slots),
    )
