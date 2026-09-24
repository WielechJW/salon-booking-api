from datetime import timedelta

from fastapi import APIRouter, HTTPException

import app.data as data
from app.schemas.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentStatusUpdate,
)


router = APIRouter(prefix="/appointments", tags=["appointments"])


def get_next_appointment_id():
    if not data.appointments:
        return 1

    return max(appointment["id"] for appointment in data.appointments) + 1


@router.get("")
def get_appointments(
    employee_id: int | None = None,
    status: AppointmentStatus | None = None,
):
    appointments = data.appointments

    if employee_id is not None:
        appointments = [
            appointment
            for appointment in appointments
            if appointment["employee_id"] == employee_id
        ]

    if status is not None:
        appointments = [
            appointment
            for appointment in appointments
            if appointment["status"] == status
        ]

    return appointments


@router.get("/{appointment_id}")
def get_appointment(appointment_id: int):
    for appointment in data.appointments:
        if appointment["id"] == appointment_id:
            return appointment

    raise HTTPException(status_code=404, detail="Appointment not found")


@router.post("", status_code=201)
def create_appointment(appointment: Appointment):
    employee_exists = any(
        employee["id"] == appointment.employee_id for employee in data.employees
    )

    if not employee_exists:
        raise HTTPException(status_code=404, detail="Employee not found")

    selected_service = next(
        (
            service
            for service in data.services
            if service["id"] == appointment.service_id
        ),
        None,
    )

    if selected_service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    new_start = appointment.start_at
    new_end = new_start + timedelta(
        minutes=selected_service["duration_minutes"]
    )

    for existing_appointment in data.appointments:
        if existing_appointment["employee_id"] != appointment.employee_id:
            continue

        if existing_appointment["status"] == "cancelled":
            continue

        existing_service = next(
            (
                service
                for service in data.services
                if service["id"] == existing_appointment["service_id"]
            ),
            None,
        )

        if existing_service is None:
            continue

        existing_start = existing_appointment["start_at"]
        existing_end = existing_start + timedelta(
            minutes=existing_service["duration_minutes"]
        )

        appointments_overlap = new_start < existing_end and new_end > existing_start

        if appointments_overlap:
            raise HTTPException(
                status_code=409,
                detail="Employee already has an appointment at this time",
            )

    new_appointment = {
        "id": get_next_appointment_id(),
        **appointment.model_dump(),
        "status": "pending",
    }

    data.appointments.append(new_appointment)

    return new_appointment


@router.patch("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
):
    for appointment in data.appointments:
        if appointment["id"] == appointment_id:
            appointment["status"] = status_update.status
            return appointment

    raise HTTPException(status_code=404, detail="Appointment not found")
