from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schedule import ScheduleModel
from app.services.booking_service import (
    get_bookable_service,
    get_overlapping_appointments,
    time_ranges_overlap,
)
from app.timezone import as_utc, get_salon_timezone


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
) -> Availability:
    selected_service = get_bookable_service(
        database_session=database_session,
        employee_id=employee_id,
        service_id=service_id,
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

    salon_timezone = get_salon_timezone()
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

    service_duration = timedelta(minutes=selected_service.duration_minutes)
    available_slots = []
    slot_start = work_start

    while slot_start + service_duration <= work_end:
        slot_end = slot_start + service_duration
        overlaps_appointment = any(
            time_ranges_overlap(
                slot_start,
                slot_end,
                appointment.start_at,
                appointment.end_at,
            )
            for appointment in appointments
        )

        if not overlaps_appointment:
            available_slots.append(
                slot_start.astimezone(salon_timezone).time().replace(tzinfo=None)
            )

        slot_start += service_duration

    return Availability(
        employee_id=employee_id,
        service_id=service_id,
        date=target_date,
        available_slots=tuple(available_slots),
    )
