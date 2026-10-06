import os
from concurrent.futures import ThreadPoolExecutor
from datetime import time
from threading import Barrier
from time import sleep

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.appointment import AppointmentModel
from app.models.schedule import ScheduleModel

POSTGRES_TESTS_ENABLED = os.getenv(
    "TEST_DATABASE_URL",
    "",
).startswith("postgresql")


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
    timezone_offset: str = "+02:00",
) -> dict:
    return {
        "employee_id": employee_id,
        "service_id": service_id,
        "start_at": f"{start_at}{timezone_offset}",
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

    assert created["start_at"] == "2026-09-25T08:45:00Z"


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
    assert response.json() == {"detail": "Employee does not provide this service"}


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

    assert created["duration_minutes"] == 45
    assert created["price"] == 80.0
    assert created["start_at"] == "2026-09-25T10:00:00Z"
    assert created["end_at"] == "2026-09-25T10:45:00Z"

    get_response = client.get(f"/appointments/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]

    filtered_response = client.get(
        "/appointments",
        params={"employee_id": 1, "status": "pending"},
    )
    assert filtered_response.status_code == 200
    assert [appointment["id"] for appointment in filtered_response.json()] == [
        created["id"]
    ]

    empty_response = client.get(
        "/appointments",
        params={"employee_id": 2, "status": "pending"},
    )
    assert empty_response.status_code == 200
    assert empty_response.json() == []


def test_appointment_keeps_service_snapshot_after_service_update(client):
    created = post_appointment(client, "2026-09-25T10:00:00")

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

    get_response = client.get(f"/appointments/{created['id']}")
    assert get_response.status_code == 200
    appointment = get_response.json()
    assert appointment["duration_minutes"] == 45
    assert appointment["price"] == 80.0
    assert appointment["end_at"] == "2026-09-25T08:45:00Z"

    conflict_response = client.post(
        "/appointments",
        json=make_appointment(
            "2026-09-25T10:30:00",
            service_id=2,
        ),
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "detail": "Employee already has an appointment at this time"
    }


def test_appointment_on_day_off_is_rejected(client):
    response = client.post(
        "/appointments",
        json=make_appointment("2026-09-26T10:00:00"),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Employee does not work on this day"}


def test_appointment_requires_timezone_offset(client):
    response = client.post(
        "/appointments",
        json=make_appointment(
            "2026-09-25T10:00:00",
            timezone_offset="",
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "start_at"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("client_name", "  \t\n"),
        ("client_name", " A "),
        ("client_email", "abcde"),
        ("client_email", "jan@@example.com"),
        ("client_phone", "abcdefg"),
        ("client_phone", "123456"),
        ("client_phone", "+1234567890123456"),
        ("client_phone", "123+456789"),
        ("client_phone", "++48123456789"),
        ("client_phone", "１２３４５６７８９"),
    ],
)
def test_appointment_rejects_invalid_contact_details(client, field, value):
    payload = make_appointment("2026-09-25T10:00:00")
    payload[field] = value

    response = client.post("/appointments", json=payload)

    assert response.status_code == 422
    assert {error["loc"][-1] for error in response.json()["detail"]} == {field}
    assert client.get("/appointments").json() == []


@pytest.mark.parametrize(
    ("phone", "normalized_phone"),
    [
        ("1234567", "1234567"),
        ("+123456789012345", "+123456789012345"),
        (" +48 (123) 456-789 ", "+48123456789"),
    ],
)
def test_appointment_normalizes_and_persists_contact_details(
    client, phone, normalized_phone
):
    payload = make_appointment("2026-09-25T10:00:00")
    payload.update(
        client_name="  Jan Kowalski  ",
        client_email="  jan@EXAMPLE.COM  ",
        client_phone=phone,
    )

    response = client.post("/appointments", json=payload)

    assert response.status_code == 201
    created = response.json()
    stored = client.get(f"/appointments/{created['id']}").json()
    for appointment in (created, stored):
        assert appointment["client_name"] == "Jan Kowalski"
        assert appointment["client_email"] == "jan@example.com"
        assert appointment["client_phone"] == normalized_phone


def test_appointment_in_the_past_is_rejected(client):
    response = client.post(
        "/appointments",
        json=make_appointment("2026-09-24T10:00:00"),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot book an appointment in the past"}


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

    assert created["start_at"] == "2026-09-25T15:15:00Z"


def test_appointment_status_follows_allowed_transitions(client):
    created = post_appointment(client, "2026-09-25T10:00:00")
    appointment_url = f"/appointments/{created['id']}/status"

    confirmed_response = client.patch(
        appointment_url,
        json={"status": "confirmed"},
    )
    assert confirmed_response.status_code == 200
    assert confirmed_response.json()["status"] == "confirmed"

    completed_response = client.patch(
        appointment_url,
        json={"status": "completed"},
    )
    assert completed_response.status_code == 200
    assert completed_response.json()["status"] == "completed"

    rejected_response = client.patch(
        appointment_url,
        json={"status": "pending"},
    )
    assert rejected_response.status_code == 409
    assert rejected_response.json() == {
        "detail": "Cannot change appointment status from completed to pending"
    }


def test_appointment_cannot_skip_status_transition(client):
    created = post_appointment(client, "2026-09-25T10:00:00")

    response = client.patch(
        f"/appointments/{created['id']}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot change appointment status from pending to completed"
    }


@pytest.mark.skipif(
    not POSTGRES_TESTS_ENABLED,
    reason="Row-level locking requires PostgreSQL",
)
@pytest.mark.postgres
def test_concurrent_overlapping_appointments_are_rejected_atomically(
    database_session,
    monkeypatch,
    admin_headers,
):
    test_engine = database_session.get_bind()
    original_add = Session.add

    def delayed_appointment_add(self, instance, _warn=True):
        if isinstance(instance, AppointmentModel):
            sleep(0.2)

        return original_add(self, instance, _warn=_warn)

    monkeypatch.setattr(Session, "add", delayed_appointment_add)

    def override_get_db():
        with Session(test_engine) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    request_barrier = Barrier(2)

    def create_concurrently(test_client):
        request_barrier.wait(timeout=5)
        return test_client.post(
            "/appointments",
            json=make_appointment("2026-09-25T10:00:00"),
        )

    try:
        with (
            TestClient(app, headers=admin_headers) as first_client,
            TestClient(app, headers=admin_headers) as second_client,
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            futures = [
                executor.submit(create_concurrently, first_client),
                executor.submit(create_concurrently, second_client),
            ]
            responses = [future.result(timeout=10) for future in futures]
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert sorted(response.status_code for response in responses) == [201, 409]

    conflict_response = next(
        response for response in responses if response.status_code == 409
    )
    assert conflict_response.json() == {
        "detail": "Employee already has an appointment at this time"
    }

    appointment_count = database_session.scalar(select(func.count(AppointmentModel.id)))
    assert appointment_count == 1
