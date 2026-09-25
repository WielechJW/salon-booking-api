import pytest
from fastapi import HTTPException

from app.routers.appointments import (
    create_appointment,
    get_appointment,
    get_appointments,
    update_appointment_status,
)
from app.schemas.appointment import (
    Appointment,
    AppointmentStatusUpdate,
)


def make_appointment(
    start_at: str,
    employee_id: int = 1,
    service_id: int = 1,
) -> Appointment:
    return Appointment(
        employee_id=employee_id,
        service_id=service_id,
        start_at=start_at,
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
    )


def test_overlapping_appointment_is_rejected(database_session):
    create_appointment(
        make_appointment("2026-09-25T10:00:00"),
        database_session,
    )

    with pytest.raises(HTTPException) as error:
        create_appointment(
            make_appointment("2026-09-25T10:30:00", service_id=2),
            database_session,
        )

    assert error.value.status_code == 409


def test_adjacent_appointment_is_allowed(database_session):
    create_appointment(
        make_appointment("2026-09-25T10:00:00"),
        database_session,
    )
    created_appointment = create_appointment(
        make_appointment("2026-09-25T10:45:00", service_id=2),
        database_session,
    )

    assert created_appointment.start_at.hour == 10
    assert created_appointment.start_at.minute == 45


def test_appointment_for_unassigned_service_is_rejected(database_session):
    with pytest.raises(HTTPException) as error:
        create_appointment(
            make_appointment(
                "2026-09-25T11:00:00",
                employee_id=2,
                service_id=1,
            ),
            database_session,
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Employee does not provide this service"


def test_cancelled_appointment_does_not_block_time(database_session):
    created_appointment = create_appointment(
        make_appointment("2026-09-25T10:00:00"),
        database_session,
    )

    update_appointment_status(
        created_appointment.id,
        AppointmentStatusUpdate(status="cancelled"),
        database_session,
    )

    new_appointment = create_appointment(
        make_appointment("2026-09-25T10:00:00"),
        database_session,
    )

    assert new_appointment.id != created_appointment.id


def test_appointment_is_persisted_and_filterable(database_session):
    created = create_appointment(
        make_appointment("2026-09-25T12:00:00"),
        database_session,
    )

    fetched = get_appointment(created.id, database_session)
    filtered = get_appointments(
        employee_id=1,
        status="pending",
        database_session=database_session,
    )

    assert fetched.id == created.id
    assert [appointment.id for appointment in filtered] == [created.id]
    assert (
        get_appointments(
            employee_id=2,
            status="pending",
            database_session=database_session,
        )
        == []
    )
