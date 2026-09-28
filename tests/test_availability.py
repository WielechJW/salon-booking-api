from datetime import time

from app.models.schedule import ScheduleModel


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


def make_appointment(start_at: str) -> dict:
    return {
        "employee_id": 1,
        "service_id": 1,
        "start_at": start_at,
        "client_name": "Jan Kowalski",
        "client_email": "jan@example.com",
        "client_phone": "123456789",
    }


def get_availability(client):
    return client.get(
        "/employees/1/availability",
        params={
            "date": "2026-09-25",
            "service_id": 1,
        },
    )


def test_availability_contains_slots_for_entire_shift(
    client,
    database_session,
):
    add_friday_schedule(database_session)

    response = get_availability(client)

    assert response.status_code == 200
    assert response.json() == {
        "employee_id": 1,
        "service_id": 1,
        "date": "2026-09-25",
        "available_slots": [
            "09:00:00",
            "09:45:00",
            "10:30:00",
            "11:15:00",
        ],
    }


def test_booked_slot_is_not_available(client, database_session):
    add_friday_schedule(database_session)
    appointment_response = client.post(
        "/appointments",
        json=make_appointment("2026-09-25T09:45:00"),
    )
    assert appointment_response.status_code == 201

    response = get_availability(client)

    assert response.status_code == 200
    assert response.json()["available_slots"] == [
        "09:00:00",
        "10:30:00",
        "11:15:00",
    ]


def test_cancelled_appointment_does_not_block_slot(
    client,
    database_session,
):
    add_friday_schedule(database_session)
    appointment_response = client.post(
        "/appointments",
        json=make_appointment("2026-09-25T09:45:00"),
    )
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]

    status_response = client.patch(
        f"/appointments/{appointment_id}/status",
        json={"status": "cancelled"},
    )
    assert status_response.status_code == 200

    response = get_availability(client)

    assert response.status_code == 200
    assert "09:45:00" in response.json()["available_slots"]


def test_day_without_schedule_has_no_available_slots(client):
    response = client.get(
        "/employees/1/availability",
        params={
            "date": "2026-09-26",
            "service_id": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["available_slots"] == []


def test_availability_rejects_unassigned_service(client):
    response = client.get(
        "/employees/2/availability",
        params={
            "date": "2026-09-25",
            "service_id": 1,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Employee does not provide this service"
    }
