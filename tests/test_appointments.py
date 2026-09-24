from copy import deepcopy

import pytest
from fastapi import HTTPException

from app import data
from app.routers.appointments import (
    create_appointment,
    update_appointment_status,
)
from app.schemas.appointment import (
    Appointment,
    AppointmentStatusUpdate,
)


@pytest.fixture(autouse=True)
def restore_appointments():
    original_appointments = deepcopy(data.appointments)
    data.appointments.clear()

    yield

    data.appointments[:] = original_appointments


def test_overlapping_appointment_is_rejected():
    first_appointment = Appointment(
        employee_id=1,
        service_id=1,
        start_at="2026-09-25T10:00:00",
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
    )

    overlapping_appointment = Appointment(
        employee_id=1,
        service_id=2,
        start_at="2026-09-25T10:30:00",
        client_name="Anna Nowak",
        client_email="anna@example.com",
        client_phone="987654321",
    )

    create_appointment(first_appointment)

    with pytest.raises(HTTPException) as error:
        create_appointment(overlapping_appointment)

    assert error.value.status_code == 409

def test_adjacent_appointment_is_allowed():
    first_appointment = Appointment(
        employee_id=1,
        service_id=1,
        start_at="2026-09-25T10:00:00",
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
    )

    adjacent_appointment = Appointment(
        employee_id=1,
        service_id=2,
        start_at="2026-09-25T10:45:00",
        client_name="Anna Nowak",
        client_email="anna@example.com",
        client_phone="987654321",
    )

    create_appointment(first_appointment)
    created_appointment = create_appointment(adjacent_appointment)

    assert created_appointment["start_at"] == adjacent_appointment.start_at
    assert len(data.appointments) == 2

def test_cancelled_appointment_does_not_block_time():
    first_appointment = Appointment(
        employee_id=1,
        service_id=1,
        start_at="2026-09-25T10:00:00",
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
    )

    created_appointment = create_appointment(first_appointment)

    update_appointment_status(
        created_appointment["id"],
        AppointmentStatusUpdate(status="cancelled"),
    )

    new_appointment = create_appointment(first_appointment)

    assert new_appointment["id"] == 2
    assert len(data.appointments) == 2