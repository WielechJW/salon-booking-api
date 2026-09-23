from fastapi import APIRouter, HTTPException
from app.schemas.appointment import Appointment, AppointmentStatusUpdate
import app.data as data


router = APIRouter(prefix="/appointments", tags=["appointments"])

def get_next_appointment_id():
    if not data.appointments:
        return 1

    return max(appointment["id"] for appointment in data.appointments) + 1


@router.get("")
def get_appointments(employee_id: int | None = None):
    if employee_id is None:
        return data.appointments

    return [
        appointment
        for appointment in data.appointments
        if appointment["employee_id"] == employee_id
    ]

@router.get("/{appointment_id}")
def get_appointment(appointment_id: int):
    for appointment in data.appointments:
        if appointment["id"] == appointment_id:
            return appointment

    raise HTTPException(status_code=404, detail="Appointment not found")

@router.post("", status_code=201)
def create_appointment(appointment: Appointment):
    employee_exists = any(
        employee["id"] == appointment.employee_id
        for employee in data.employees
    )

    if not employee_exists:
        raise HTTPException(status_code=404, detail="Employee not found")

    service_exists = any(
        service["id"] == appointment.service_id
        for service in data.services
    )

    if not service_exists:
        raise HTTPException(status_code=404, detail="Service not found")

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