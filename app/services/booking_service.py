from datetime import datetime, timedelta
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.schedule import ScheduleModel
from app.models.service import ServiceModel
from app.services.calendar_service import (
    get_overlapping_appointments,
    get_overlapping_time_offs,
    lock_employee_calendar,
)
from app.services.calendar_service import (
    time_ranges_overlap as time_ranges_overlap,
)
from app.services.errors import (
    DomainConflictError,
    DomainNotFoundError,
    DomainValidationError,
)
from app.timezone import as_utc, get_salon_timezone, utc_now

AppointmentStatus = Literal[
    "pending",
    "confirmed",
    "cancelled",
    "completed",
]

APPOINTMENT_STATUSES: frozenset[str] = frozenset(
    {"pending", "confirmed", "cancelled", "completed"}
)
ALLOWED_STATUS_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "cancelled": set(),
    "completed": set(),
}


def get_bookable_service(
    *,
    database_session: Session,
    employee_id: int,
    service_id: int,
) -> ServiceModel:
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise DomainNotFoundError("Employee not found")

    selected_service = database_session.get(ServiceModel, service_id)

    if selected_service is None:
        raise DomainNotFoundError("Service not found")

    assignment = database_session.get(
        EmployeeServiceModel,
        (employee_id, service_id),
    )

    if assignment is None:
        raise DomainConflictError("Employee does not provide this service")

    return selected_service


def create_appointment(
    *,
    database_session: Session,
    employee_id: int,
    service_id: int,
    start_at: datetime,
    client_name: str,
    client_email: str,
    client_phone: str,
    current_time: datetime | None = None,
) -> AppointmentModel:
    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise DomainValidationError("start_at must include a timezone offset")

    selected_service = get_bookable_service(
        database_session=database_session,
        employee_id=employee_id,
        service_id=service_id,
    )
    new_start = as_utc(start_at)
    now = as_utc(current_time) if current_time is not None else utc_now()

    if new_start < now:
        raise DomainConflictError("Cannot book an appointment in the past")

    new_end = new_start + timedelta(minutes=selected_service.duration_minutes)
    salon_timezone = get_salon_timezone()
    local_start = new_start.astimezone(salon_timezone)
    local_end = new_end.astimezone(salon_timezone)

    lock_employee_calendar(
        database_session=database_session,
        employee_id=employee_id,
    )

    work_schedule = database_session.scalar(
        select(ScheduleModel)
        .where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == local_start.weekday(),
        )
        .execution_options(populate_existing=True)
    )

    if work_schedule is None:
        raise DomainConflictError("Employee does not work on this day")

    is_outside_working_hours = (
        local_start.time().replace(tzinfo=None) < work_schedule.start_time
        or local_end.date() != local_start.date()
        or local_end.time().replace(tzinfo=None) > work_schedule.end_time
    )

    if is_outside_working_hours:
        raise DomainConflictError("Appointment is outside employee working hours")

    conflicts = get_overlapping_appointments(
        database_session=database_session,
        employee_id=employee_id,
        start_at=new_start,
        end_at=new_end,
    )

    if conflicts:
        raise DomainConflictError("Employee already has an appointment at this time")

    time_offs = get_overlapping_time_offs(
        database_session=database_session,
        employee_id=employee_id,
        start_at=new_start,
        end_at=new_end,
    )

    if time_offs:
        raise DomainConflictError("Employee is unavailable at this time")

    new_appointment = AppointmentModel(
        employee_id=employee_id,
        service_id=service_id,
        start_at=new_start,
        end_at=new_end,
        duration_minutes=selected_service.duration_minutes,
        price=selected_service.price,
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        status="pending",
    )

    database_session.add(new_appointment)
    database_session.commit()
    database_session.refresh(new_appointment)

    return new_appointment


def update_appointment_status(
    *,
    database_session: Session,
    appointment_id: int,
    requested_status: AppointmentStatus,
) -> AppointmentModel:
    if requested_status not in APPOINTMENT_STATUSES:
        raise DomainValidationError("Unknown appointment status")

    appointment = database_session.scalar(
        select(AppointmentModel)
        .where(AppointmentModel.id == appointment_id)
        .with_for_update()
    )

    if appointment is None:
        raise DomainNotFoundError("Appointment not found")

    current_status = cast(AppointmentStatus, appointment.status)

    if (
        requested_status != current_status
        and requested_status not in ALLOWED_STATUS_TRANSITIONS[current_status]
    ):
        raise DomainConflictError(
            "Cannot change appointment status "
            f"from {current_status} to {requested_status}"
        )

    if requested_status == current_status:
        return appointment

    appointment.status = requested_status
    database_session.commit()
    database_session.refresh(appointment)

    return appointment
