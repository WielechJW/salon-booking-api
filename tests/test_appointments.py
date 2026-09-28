from datetime import time

import pytest

from app.models.schedule import ScheduleModel


@pytest.fixture(autouse=True)
def add_work_schedule(database_session):
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
    )
    database_session.commit()


def make_appointment(
    start_at: str,
    employee_id: int = 1,
    service_id: int = 1,
) -> dict:
    return {
        "employee_id": employee_id,
        "service_id": service_id,
        "start_at": start_at,
        "client_name": "Jan Kowalski",
        "client_email": "jan@example.com",
        "client_phone": "123456789",
    }


def post_appointment(
    client,
    start_at: str,
    employee_id: int = 1,
    service_id: int = 1,
) -> dict:
    response = client.post(
        "/appointments",
        json=make_appointment(
            start_at,
            employee_id=employee_id,
            service_id=service_id,
        ),
    )
    assert response.status_code == 201
    return response.json()


def test_overlapping_appointment_is_rejected(client):
    post_appointment(client, "2026-09-25T10:00:00")

    response = client.post(
        "/appointments",
        json=make_appointment(
            "2026-09-25T10:30:00",
            service_id=2,
        ),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Employee already has an appointment at this time"
    }


def test_adjacent_appointment_is_allowed(client):
    post_appointment(client, "2026-09-25T10:00:00")

    created = post_appointment(
        client,
        "2026-09-25T10:45:00",
        service_id=2,
    )

    assert created["start_at"] == "2026-09-25T10:45:00"


def test_appointment_for_unassigned_service_is_rejected(client):
    response = client.post(
        "/appointments",
        json=make_appointment(
            "2026-09-25T11:00:00",
            employee_id=2,
            service_id=1,
        ),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Employee does not provide this service"
    }


def test_cancelled_appointment_does_not_block_time(client):
    created = post_appointment(client, "2026-09-25T10:00:00")

    status_response = client.patch(
        f"/appointments/{created['id']}/status",
        json={"status": "cancelled"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "cancelled"

    new_appointment = post_appointment(
        client,
        "2026-09-25T10:00:00",
    )

    assert new_appointment["id"] != created["id"]


def test_appointment_is_persisted_and_filterable(client):
    created = post_appointment(client, "2026-09-25T12:00:00")

    get_response = client.get(f"/appointments/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]

    filtered_response = client.get(
        "/appointments",
        params={"employee_id": 1, "status": "pending"},
    )
    assert filtered_response.status_code == 200
    assert [
        appointment["id"] for appointment in filtered_response.json()
    ] == [created["id"]]

    empty_response = client.get(
        "/appointments",
        params={"employee_id": 2, "status": "pending"},
    )
    assert empty_response.status_code == 200
    assert empty_response.json() == []


def test_appointment_on_day_off_is_rejected(client):
    response = client.post(
        "/appointments",
        json=make_appointment("2026-09-26T10:00:00"),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Employee does not work on this day"
    }


@pytest.mark.parametrize(
    "start_at",
    [
        "2026-09-25T08:30:00",
        "2026-09-25T17:30:00",
    ],
)
def test_appointment_outside_working_hours_is_rejected(
    client,
    start_at,
):
    response = client.post(
        "/appointments",
        json=make_appointment(start_at),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Appointment is outside employee working hours"
    }


def test_appointment_ending_at_work_end_is_allowed(client):
    created = post_appointment(client, "2026-09-25T17:15:00")

    assert created["start_at"] == "2026-09-25T17:15:00"
