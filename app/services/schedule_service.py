from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.schedule import ScheduleModel
from app.services.calendar_service import lock_employee_calendar
from app.services.errors import DomainConflictError, DomainNotFoundError
from app.timezone import as_utc, get_salon_timezone, utc_now


def update_employee_schedule(
    *,
    database_session: Session,
    employee_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    current_time: datetime | None = None,
) -> ScheduleModel:
    if database_session.get(EmployeeModel, employee_id) is None:
        raise DomainNotFoundError("Employee not found")

    lock_employee_calendar(
        database_session=database_session,
        employee_id=employee_id,
    )
    schedule = database_session.scalar(
        select(ScheduleModel)
        .where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == day_of_week,
        )
        .execution_options(populate_existing=True)
    )

    if schedule is None:
        raise DomainNotFoundError("Schedule for this day not found")

    now = as_utc(current_time) if current_time is not None else utc_now()
    appointments = database_session.execute(
        select(AppointmentModel.start_at, AppointmentModel.end_at).where(
            AppointmentModel.employee_id == employee_id,
            AppointmentModel.status.in_(("pending", "confirmed")),
            AppointmentModel.end_at > now,
        )
    )
    salon_timezone = get_salon_timezone()

    for appointment_start, appointment_end in appointments:
        local_start = as_utc(appointment_start).astimezone(salon_timezone)
        local_end = as_utc(appointment_end).astimezone(salon_timezone)

        if local_start.weekday() != day_of_week:
            continue

        if (
            local_start.time().replace(tzinfo=None) < start_time
            or local_end.date() != local_start.date()
            or local_end.time().replace(tzinfo=None) > end_time
        ):
            raise DomainConflictError(
                "Schedule change would leave an active appointment "
                "outside employee working hours"
            )

    schedule.start_time = start_time
    schedule.end_time = end_time
    database_session.commit()
    database_session.refresh(schedule)
    return schedule
