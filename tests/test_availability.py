from datetime import datetime, time

import pytest

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
        "start_at": f"{start_at}+02:00",
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
            "09:15:00",
            "09:30:00",
            "09:45:00",
            "10:00:00",
            "10:15:00",
            "10:30:00",
            "10:45:00",
            "11:00:00",
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
        "10:45:00",
        "11:00:00",
        "11:15:00",
    ]


def test_slot_immediately_after_off_grid_booking_can_be_booked(
    client, database_session
):
    add_friday_schedule(database_session)
    assert (
        client.post(
            "/appointments",
            json=make_appointment("2026-09-25T10:00:00"),
        ).status_code
        == 201
    )

    response = get_availability(client)

    assert response.status_code == 200
    assert "10:45:00" in response.json()["available_slots"]
    assert "10:30:00" not in response.json()["available_slots"]
    assert (
        client.post(
            "/appointments",
            json=make_appointment("2026-09-25T10:45:00"),
        ).status_code
        == 201
    )


@pytest.mark.parametrize(
    ("current_time", "first_slot", "slot_count"),
    [
        ("2026-09-24T22:00:00Z", "09:00:00", 10),
        ("2026-09-25T07:00:00Z", "09:00:00", 10),
        ("2026-09-25T07:07:00Z", "09:15:00", 9),
        ("2026-09-25T09:15:00Z", "11:15:00", 1),
        ("2026-09-25T09:15:01Z", None, 0),
        ("2026-09-25T22:00:00Z", None, 0),
        ("2026-09-26T07:00:00Z", None, 0),
    ],
)
def test_availability_only_contains_present_and_future_slots(
    client, database_session, monkeypatch, current_time, first_slot, slot_count
):
    add_friday_schedule(database_session)
    monkeypatch.setattr(
        "app.routers.availability.utc_now",
        lambda: datetime.fromisoformat(current_time),
    )

    response = get_availability(client)

    assert response.status_code == 200
    slots = response.json()["available_slots"]
    assert len(slots) == slot_count
    if first_slot is not None:
        assert slots[0] == first_slot
        assert slots[-1] == "11:15:00"


@pytest.mark.parametrize(
    ("duration_minutes", "last_slot", "slot_count"),
    [(20, "11:30:00", 11), (60, "11:00:00", 9), (181, None, 0)],
)
def test_slot_step_is_independent_of_duration_and_service_fits_shift(
    client, database_session, duration_minutes, last_slot, slot_count
):
    add_friday_schedule(database_session)
    assert (
        client.put(
            "/services/1",
            json={
                "name": "Strzyżenie",
                "description": "Usługa o zmienionym czasie trwania",
                "duration_minutes": duration_minutes,
                "price": 80,
            },
        ).status_code
        == 200
    )

    response = get_availability(client)

    assert response.status_code == 200
    slots = response.json()["available_slots"]
    assert len(slots) == slot_count
    if last_slot is not None:
        assert slots[:2] == ["09:00:00", "09:15:00"]
        assert slots[-1] == last_slot


def test_availability_uses_appointment_snapshot_after_service_update(
    client,
    database_session,
):
    add_friday_schedule(database_session)
    appointment_response = client.post(
        "/appointments",
        json=make_appointment("2026-09-25T09:45:00"),
    )
    assert appointment_response.status_code == 201

    update_response = client.put(
        "/services/1",
        json={
            "name": "Strzyżenie męskie ekspresowe",
            "description": "Krótszy wariant tej samej usługi",
            "duration_minutes": 15,
            "price": 50,
        },
    )
    assert update_response.status_code == 200

    response = get_availability(client)

    assert response.status_code == 200
    available_slots = response.json()["available_slots"]
    assert "10:15:00" not in available_slots
    assert "10:30:00" in available_slots


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
    assert response.json() == {"detail": "Employee does not provide this service"}
