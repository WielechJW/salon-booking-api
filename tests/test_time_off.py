import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timezone
from threading import Barrier
from time import sleep

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.appointment import AppointmentModel
from app.models.employee_time_off import EmployeeTimeOffModel
from app.models.schedule import ScheduleModel

POSTGRES_TESTS_ENABLED = os.getenv(
    "TEST_DATABASE_URL",
    "",
).startswith("postgresql")


def add_friday_schedule(database_session) -> None:
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9),
            end_time=time(18),
        )
    )
    database_session.commit()


def make_time_off(
    start_at: str = "2026-09-25T10:00:00+02:00",
    end_at: str = "2026-09-25T11:00:00+02:00",
    reason: str = "Przerwa prywatna",
) -> dict:
    return {
        "start_at": start_at,
        "end_at": end_at,
        "reason": reason,
    }


def make_appointment(start_at: str = "2026-09-25T10:00:00+02:00") -> dict:
    return {
        "employee_id": 1,
        "service_id": 1,
        "start_at": start_at,
        "client_name": "Jan Kowalski",
        "client_email": "jan@example.com",
        "client_phone": "123456789",
    }


def create_time_off(client, **overrides) -> dict:
    payload = make_time_off(**overrides)
    response = client.post("/employees/1/time-off", json=payload)
    assert response.status_code == 201
    return response.json()


def test_time_off_crud_normalizes_timestamps_to_utc(client):
    created = create_time_off(client)

    assert created == {
        "id": 1,
        "employee_id": 1,
        "start_at": "2026-09-25T08:00:00Z",
        "end_at": "2026-09-25T09:00:00Z",
        "reason": "Przerwa prywatna",
    }

    list_response = client.get("/employees/1/time-off")
    assert list_response.status_code == 200
    assert list_response.json() == [created]

    update_response = client.put(
        "/employees/1/time-off/1",
        json=make_time_off(
            start_at="2026-09-25T13:00:00+02:00",
            end_at="2026-09-25T15:00:00+02:00",
            reason="Szkolenie",
        ),
    )
    assert update_response.status_code == 200
    assert update_response.json()["start_at"] == "2026-09-25T11:00:00Z"
    assert update_response.json()["end_at"] == "2026-09-25T13:00:00Z"
    assert update_response.json()["reason"] == "Szkolenie"

    delete_response = client.delete("/employees/1/time-off/1")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Time off deleted successfully"}
    assert client.get("/employees/1/time-off").json() == []


def test_time_off_list_is_sorted_by_start_time(client):
    later = create_time_off(
        client,
        start_at="2026-09-26T13:00:00+02:00",
        end_at="2026-09-26T14:00:00+02:00",
    )
    earlier = create_time_off(
        client,
        start_at="2026-09-25T13:00:00+02:00",
        end_at="2026-09-25T14:00:00+02:00",
    )

    response = client.get("/employees/1/time-off")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [earlier["id"], later["id"]]


@pytest.mark.parametrize(
    "payload",
    [
        make_time_off(
            start_at="2026-09-25T10:00:00",
            end_at="2026-09-25T11:00:00",
        ),
        make_time_off(
            start_at="2026-09-25T11:00:00+02:00",
            end_at="2026-09-25T10:00:00+02:00",
        ),
    ],
)
def test_time_off_rejects_invalid_time_range(client, payload):
    response = client.post("/employees/1/time-off", json=payload)

    assert response.status_code == 422


def test_time_off_requires_existing_employee(client):
    response = client.post("/employees/999/time-off", json=make_time_off())

    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}


def test_overlapping_time_off_is_rejected_but_adjacent_period_is_allowed(client):
    create_time_off(client)

    overlap_response = client.post(
        "/employees/1/time-off",
        json=make_time_off(
            start_at="2026-09-25T10:30:00+02:00",
            end_at="2026-09-25T11:30:00+02:00",
        ),
    )
    adjacent_response = client.post(
        "/employees/1/time-off",
        json=make_time_off(
            start_at="2026-09-25T11:00:00+02:00",
            end_at="2026-09-25T12:00:00+02:00",
        ),
    )

    assert overlap_response.status_code == 409
    assert overlap_response.json() == {
        "detail": "Time off overlaps an existing time off"
    }
    assert adjacent_response.status_code == 201


def test_time_off_conflicts_with_active_appointment_but_not_cancelled_one(
    client, database_session
):
    add_friday_schedule(database_session)

    appointment_response = client.post("/appointments", json=make_appointment())
    assert appointment_response.status_code == 201

    conflict_response = client.post(
        "/employees/1/time-off",
        json=make_time_off(
            start_at="2026-09-25T10:30:00+02:00",
            end_at="2026-09-25T11:30:00+02:00",
        ),
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "detail": "Time off overlaps an existing appointment"
    }

    appointment_id = appointment_response.json()["id"]
    cancel_response = client.patch(
        f"/appointments/{appointment_id}/status",
        json={"status": "cancelled"},
    )
    assert cancel_response.status_code == 200

    allowed_response = client.post(
        "/employees/1/time-off",
        json=make_time_off(
            start_at="2026-09-25T10:30:00+02:00",
            end_at="2026-09-25T11:30:00+02:00",
        ),
    )
    assert allowed_response.status_code == 201


def test_time_off_blocks_new_appointment(client, database_session):
    add_friday_schedule(database_session)
    create_time_off(client)

    response = client.post(
        "/appointments",
        json=make_appointment("2026-09-25T10:15:00+02:00"),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Employee is unavailable at this time"}


def test_time_off_removes_slot_from_availability(client, database_session):
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9),
            end_time=time(12),
        )
    )
    database_session.commit()
    create_time_off(
        client,
        start_at="2026-09-25T09:45:00+02:00",
        end_at="2026-09-25T10:30:00+02:00",
    )

    response = client.get(
        "/employees/1/availability",
        params={"date": "2026-09-25", "service_id": 1},
    )

    assert response.status_code == 200
    assert response.json()["available_slots"] == [
        "09:00:00",
        "10:30:00",
        "10:45:00",
        "11:00:00",
        "11:15:00",
    ]


def test_database_rejects_invalid_time_off_range(database_session):
    database_session.add(
        EmployeeTimeOffModel(
            employee_id=1,
            start_at=datetime(2026, 9, 25, 10, tzinfo=timezone.utc),
            end_at=datetime(2026, 9, 25, 9, tzinfo=timezone.utc),
            reason="Niepoprawny zakres",
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()

    database_session.rollback()


@pytest.mark.skipif(
    not POSTGRES_TESTS_ENABLED,
    reason="Row-level locking requires PostgreSQL",
)
@pytest.mark.postgres
def test_concurrent_appointment_and_time_off_are_rejected_atomically(
    database_session,
    monkeypatch,
):
    add_friday_schedule(database_session)
    test_engine = database_session.get_bind()
    original_add = Session.add

    def delayed_calendar_add(self, instance, _warn=True):
        if isinstance(instance, (AppointmentModel, EmployeeTimeOffModel)):
            sleep(0.2)

        return original_add(self, instance, _warn=_warn)

    monkeypatch.setattr(Session, "add", delayed_calendar_add)

    def override_get_db():
        with Session(test_engine) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    request_barrier = Barrier(2)

    def create_appointment_concurrently(test_client):
        request_barrier.wait(timeout=5)
        return test_client.post("/appointments", json=make_appointment())

    def create_time_off_concurrently(test_client):
        request_barrier.wait(timeout=5)
        return test_client.post("/employees/1/time-off", json=make_time_off())

    try:
        with (
            TestClient(app) as first_client,
            TestClient(app) as second_client,
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            futures = [
                executor.submit(create_appointment_concurrently, first_client),
                executor.submit(create_time_off_concurrently, second_client),
            ]
            responses = [future.result(timeout=10) for future in futures]
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert sorted(response.status_code for response in responses) == [201, 409]

    appointment_count = database_session.scalar(select(func.count(AppointmentModel.id)))
    time_off_count = database_session.scalar(
        select(func.count(EmployeeTimeOffModel.id))
    )
    assert appointment_count + time_off_count == 1
