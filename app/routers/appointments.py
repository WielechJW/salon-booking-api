from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.schemas.appointment import (
    Appointment,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)
from app.services import booking_service
from app.timezone import utc_now

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
    return booking_service.create_appointment(
        database_session=database_session,
        current_time=utc_now(),
        **appointment.model_dump(),
    )


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    database_session: Session = Depends(get_db),
):
    return booking_service.update_appointment_status(
        database_session=database_session,
        appointment_id=appointment_id,
        requested_status=status_update.status,
    )
