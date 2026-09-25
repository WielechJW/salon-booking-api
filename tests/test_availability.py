from datetime import date, time

import pytest
from fastapi import HTTPException

from app.models.schedule import ScheduleModel
from app.routers.appointments import create_appointment
from app.routers.availability import get_employee_availability
from app.schemas.appointment import Appointment


def add_friday_schedule(database_session):
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
    )
    database_session.commit()


def make_appointment(start_at: str) -> Appointment:
    return Appointment(
        employee_id=1,
        service_id=1,
        start_at=start_at,
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
    )


def test_availability_contains_slots_for_entire_shift(database_session):
    add_friday_schedule(database_session)

    availability = get_employee_availability(
        1,
        date(2026, 9, 25),
        1,
        database_session,
    )

    assert availability.available_slots == [
        time(9, 0),
        time(9, 45),
        time(10, 30),
        time(11, 15),
    ]


def test_booked_slot_is_not_available(database_session):
    add_friday_schedule(database_session)
    create_appointment(
        make_appointment("2026-09-25T09:45:00"),
        database_session,
    )

    availability = get_employee_availability(
        1,
        date(2026, 9, 25),
        1,
        database_session,
    )

    assert availability.available_slots == [
        time(9, 0),
        time(10, 30),
        time(11, 15),
    ]


def test_cancelled_appointment_does_not_block_slot(database_session):
    add_friday_schedule(database_session)
    appointment = create_appointment(
        make_appointment("2026-09-25T09:45:00"),
        database_session,
    )
    appointment.status = "cancelled"
    database_session.commit()

    availability = get_employee_availability(
        1,
        date(2026, 9, 25),
        1,
        database_session,
    )

    assert time(9, 45) in availability.available_slots


def test_day_without_schedule_has_no_available_slots(database_session):
    availability = get_employee_availability(
        1,
        date(2026, 9, 26),
        1,
        database_session,
    )

    assert availability.available_slots == []


def test_availability_rejects_unassigned_service(database_session):
    with pytest.raises(HTTPException) as error:
        get_employee_availability(
            2,
            date(2026, 9, 25),
            1,
            database_session,
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Employee does not provide this service"
