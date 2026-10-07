from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import event

from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.employee_time_off import EmployeeTimeOffModel
from app.models.schedule import ScheduleModel
from app.models.service import ServiceModel


def add_schedule(session, employee_id, start=time(9), end=time(11), weekday=4):
    session.add(
        ScheduleModel(
            employee_id=employee_id,
            day_of_week=weekday,
            start_time=start,
            end_time=end,
        )
    )


def search(client, target_date="2026-09-25", service_id=1):
    return client.get(
        "/availability", params={"date": target_date, "service_id": service_id}
    )


@pytest.fixture
def two_available_employees(database_session):
    database_session.add(EmployeeServiceModel(employee_id=2, service_id=1))
    add_schedule(database_session, 1)
    add_schedule(database_session, 2)
    database_session.commit()


def test_service_search_is_public_sorted_and_can_be_booked(
    anonymous_client, client, two_available_employees
):
    response = search(anonymous_client)
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 12
    assert slots[:2] == [
        {
            "employee_id": 1,
            "employee_name": "Anna Kowalska",
            "start_at": "2026-09-25T07:00:00Z",
            "end_at": "2026-09-25T07:45:00Z",
        },
        {
            "employee_id": 2,
            "employee_name": "Bartek Nowak",
            "start_at": "2026-09-25T07:00:00Z",
            "end_at": "2026-09-25T07:45:00Z",
        },
    ]
    assert slots == sorted(
        slots, key=lambda slot: (slot["start_at"], slot["employee_id"])
    )
    chosen = slots[1]
    assert (
        client.post(
            "/appointments",
            json={
                "employee_id": chosen["employee_id"],
                "service_id": 1,
                "start_at": chosen["start_at"],
                "client_name": "Jan Kowalski",
                "client_email": "jan@example.com",
                "client_phone": "123456789",
            },
        ).status_code
        == 201
    )
    assert chosen not in search(anonymous_client).json()


def test_search_only_includes_assigned_workers_with_schedule(
    anonymous_client, database_session
):
    add_schedule(database_session, 1)
    add_schedule(database_session, 2)
    database_session.commit()
    assert {slot["employee_id"] for slot in search(anonymous_client).json()} == {1}
    assert search(anonymous_client, target_date="2026-09-26").json() == []
    assert search(anonymous_client, target_date="2026-09-23").json() == []


def test_service_with_no_assigned_employees_returns_empty(
    anonymous_client, database_session
):
    service = ServiceModel(
        name="Unassigned", description="No employees yet", duration_minutes=30, price=50
    )
    database_session.add(service)
    database_session.commit()
    response = search(anonymous_client, service_id=service.id)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "params",
    [
        {"service_id": 0, "date": "2026-09-25"},
        {"service_id": 2147483648, "date": "2026-09-25"},
        {"service_id": 1, "date": "invalid"},
        {"date": "2026-09-25"},
        {"service_id": 1},
    ],
)
def test_invalid_service_search_parameters_return_422(anonymous_client, params):
    assert anonymous_client.get("/availability", params=params).status_code == 422


def test_missing_service_returns_404_even_for_past_date(anonymous_client):
    response = search(anonymous_client, target_date="2026-09-23", service_id=99999)
    assert response.status_code == 404
    assert response.json() == {"detail": "Service not found"}


def test_search_uses_per_employee_bookings_time_off_and_snapshot(
    client, anonymous_client, database_session, two_available_employees
):
    booking = client.post(
        "/appointments",
        json={
            "employee_id": 1,
            "service_id": 1,
            "start_at": "2026-09-25T09:00:00+02:00",
            "client_name": "Jan Kowalski",
            "client_email": "jan@example.com",
            "client_phone": "123456789",
        },
    )
    assert booking.status_code == 201
    assert (
        client.post(
            "/employees/2/time-off",
            json={
                "start_at": "2026-09-25T10:00:00+02:00",
                "end_at": "2026-09-25T11:00:00+02:00",
                "reason": "Lunch break",
            },
        ).status_code
        == 201
    )
    database_session.get(ServiceModel, 1).duration_minutes = 20
    database_session.commit()
    slots = search(anonymous_client).json()
    assert not any(
        slot["employee_id"] == 1 and slot["start_at"] < "2026-09-25T07:45:00Z"
        for slot in slots
    )
    assert any(
        slot["employee_id"] == 1 and slot["start_at"] == "2026-09-25T07:45:00Z"
        for slot in slots
    )
    assert all(
        slot["end_at"] <= "2026-09-25T08:00:00Z"
        for slot in slots
        if slot["employee_id"] == 2
    )
    for employee_id in (1, 2):
        expected = client.get(
            f"/employees/{employee_id}/availability",
            params={
                "date": "2026-09-25",
                "service_id": 1,
            },
        ).json()["available_slots"]
        actual = [
            datetime.fromisoformat(slot["start_at"])
            .astimezone(ZoneInfo("Europe/Warsaw"))
            .strftime("%H:%M:%S")
            for slot in slots
            if slot["employee_id"] == employee_id
        ]
        assert actual == expected
    assert (
        client.patch(
            f"/appointments/{booking.json()['id']}/status", json={"status": "cancelled"}
        ).status_code
        == 200
    )
    assert any(
        slot["employee_id"] == 1 and slot["start_at"] == "2026-09-25T07:00:00Z"
        for slot in search(anonymous_client).json()
    )


def test_fully_blocked_employee_is_omitted(
    anonymous_client, database_session, two_available_employees
):
    database_session.add(
        EmployeeTimeOffModel(
            employee_id=1,
            start_at=datetime.fromisoformat("2026-09-25T07:00:00Z"),
            end_at=datetime.fromisoformat("2026-09-25T09:00:00Z"),
            reason="Day off",
        )
    )
    database_session.commit()
    assert {slot["employee_id"] for slot in search(anonymous_client).json()} == {2}


def test_same_day_search_omits_past_starts(
    anonymous_client, two_available_employees, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.availability.utc_now",
        lambda: datetime.fromisoformat("2026-09-25T07:07:00Z"),
    )
    slots = search(anonymous_client).json()
    assert slots[0]["start_at"] == "2026-09-25T07:15:00Z"
    assert len(slots) == 10


def test_dst_repeated_local_hours_have_distinct_bookable_utc_starts(
    anonymous_client, client, database_session
):
    add_schedule(database_session, 1, start=time(1), end=time(4), weekday=6)
    database_session.commit()
    slots = search(anonymous_client, target_date="2026-10-25").json()
    starts = [slot["start_at"] for slot in slots]
    assert len(starts) == len(set(starts))
    assert "2026-10-25T00:00:00Z" in starts
    assert "2026-10-25T01:00:00Z" in starts
    for start in ("2026-10-25T00:00:00Z", "2026-10-25T01:00:00Z"):
        assert (
            client.post(
                "/appointments",
                json={
                    "employee_id": 1,
                    "service_id": 1,
                    "start_at": start,
                    "client_name": "Jan Kowalski",
                    "client_email": "jan@example.com",
                    "client_phone": "123456789",
                },
            ).status_code
            == 201
        )


def test_service_search_has_bounded_database_queries(
    anonymous_client, database_session
):
    for index in range(5):
        employee = EmployeeModel(name=f"Employee {index}")
        database_session.add(employee)
        database_session.flush()
        database_session.add(
            EmployeeServiceModel(employee_id=employee.id, service_id=1)
        )
        add_schedule(database_session, employee.id)
    database_session.commit()
    queries = []
    engine = database_session.get_bind()

    def record_query(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", record_query)
    try:
        response = search(anonymous_client)
    finally:
        event.remove(engine, "before_cursor_execute", record_query)
    assert response.status_code == 200
    assert len({slot["employee_id"] for slot in response.json()}) == 5
    assert len(queries) <= 4
