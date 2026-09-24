from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.service import ServiceModel
from app.schemas.appointment import (
    Appointment,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)


router = APIRouter(prefix="/appointments", tags=["appointments"])


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

    new_start = appointment.start_at
    new_end = new_start + timedelta(minutes=selected_service.duration_minutes)

    existing_query = (
        select(AppointmentModel, ServiceModel.duration_minutes)
        .join(ServiceModel, AppointmentModel.service_id == ServiceModel.id)
        .where(
            AppointmentModel.employee_id == appointment.employee_id,
            AppointmentModel.status != "cancelled",
        )
    )

    for existing_appointment, duration_minutes in database_session.execute(
        existing_query
    ):
        existing_start = existing_appointment.start_at
        existing_end = existing_start + timedelta(minutes=duration_minutes)

        if new_start < existing_end and new_end > existing_start:
            raise HTTPException(
                status_code=409,
                detail="Employee already has an appointment at this time",
            )

    new_appointment = AppointmentModel(
        **appointment.model_dump(),
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
    appointment = database_session.get(AppointmentModel, appointment_id)

    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = status_update.status
    database_session.commit()
    database_session.refresh(appointment)

    return appointment
