from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.schedule import ScheduleModel
from app.models.service import ServiceModel
from app.schemas.appointment import (
    Appointment,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)
from app.timezone import get_salon_timezone, utc_now

router = APIRouter(prefix="/appointments", tags=["appointments"])

ALLOWED_STATUS_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "cancelled": set(),
    "completed": set(),
}


def lock_employee_for_booking(
    employee_id: int,
    database_session: Session,
) -> None:
    database_session.execute(
        select(EmployeeModel.id)
        .where(EmployeeModel.id == employee_id)
        .with_for_update()
    ).scalar_one()


@router.get("", response_model=list[AppointmentResponse])
def get_appointments(
    employee_id: int | None = None,
    status: AppointmentStatus | None = None,
    database_session: Session = Depends(get_db),
):
    query = select(AppointmentModel).order_by(AppointmentModel.start_at)

    if employee_id is not None:
        query = query.where(AppointmentModel.employee_id == employee_id)

    if status is not None:
        query = query.where(AppointmentModel.status == status)

    return database_session.scalars(query).all()


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    database_session: Session = Depends(get_db),
):
    appointment = database_session.get(AppointmentModel, appointment_id)

    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment


@router.post("", status_code=201, response_model=AppointmentResponse)
def create_appointment(
    appointment: Appointment,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, appointment.employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    selected_service = database_session.get(ServiceModel, appointment.service_id)

    if selected_service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    assignment = database_session.get(
        EmployeeServiceModel,
        (appointment.employee_id, appointment.service_id),
    )

    if assignment is None:
        raise HTTPException(
            status_code=409,
            detail="Employee does not provide this service",
        )

    new_start = appointment.start_at

    if new_start < utc_now():
        raise HTTPException(
            status_code=409,
            detail="Cannot book an appointment in the past",
        )

    new_end = new_start + timedelta(minutes=selected_service.duration_minutes)
    salon_timezone = get_salon_timezone()
    local_start = new_start.astimezone(salon_timezone)
    local_end = new_end.astimezone(salon_timezone)

    work_schedule = database_session.scalar(
        select(ScheduleModel).where(
            ScheduleModel.employee_id == appointment.employee_id,
            ScheduleModel.day_of_week == local_start.weekday(),
        )
    )

    if work_schedule is None:
        raise HTTPException(
            status_code=409,
            detail="Employee does not work on this day",
        )

    is_outside_working_hours = (
        local_start.time().replace(tzinfo=None) < work_schedule.start_time
        or local_end.date() != local_start.date()
        or local_end.time().replace(tzinfo=None) > work_schedule.end_time
    )

    if is_outside_working_hours:
        raise HTTPException(
            status_code=409,
            detail="Appointment is outside employee working hours",
        )

    lock_employee_for_booking(
        employee_id=appointment.employee_id,
        database_session=database_session,
    )

    conflicting_appointment_id = database_session.scalar(
        select(AppointmentModel.id)
        .where(
            AppointmentModel.employee_id == appointment.employee_id,
            AppointmentModel.status != "cancelled",
            AppointmentModel.start_at < new_end,
            AppointmentModel.end_at > new_start,
        )
        .limit(1)
    )

    if conflicting_appointment_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Employee already has an appointment at this time",
        )

    new_appointment = AppointmentModel(
        **appointment.model_dump(),
        duration_minutes=selected_service.duration_minutes,
        price=selected_service.price,
        end_at=new_end,
        status="pending",
    )

    database_session.add(new_appointment)
    database_session.commit()
    database_session.refresh(new_appointment)

    return new_appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    database_session: Session = Depends(get_db),
):
    appointment = database_session.scalar(
        select(AppointmentModel)
        .where(AppointmentModel.id == appointment_id)
        .with_for_update()
    )

    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    current_status = appointment.status
    requested_status = status_update.status

    if (
        requested_status != current_status
        and requested_status not in ALLOWED_STATUS_TRANSITIONS[current_status]
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot change appointment status "
                f"from {current_status} to {requested_status}"
            ),
        )

    appointment.status = status_update.status
    database_session.commit()
    database_session.refresh(appointment)

    return appointment
