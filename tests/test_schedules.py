from datetime import datetime

import pytest


def make_schedule(
    day_of_week: int,
    start_time: str = "09:00:00",
    end_time: str = "17:00:00",
) -> dict:
    return {
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
    }


def test_schedule_can_be_created(client):
    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["id"] is not None
    assert created["employee_id"] == 1
    assert created["day_of_week"] == 0
    assert created["start_time"] == "09:00:00"
    assert created["end_time"] == "17:00:00"


def test_employee_schedule_is_sorted_by_day(client):
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(day_of_week=2),
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(day_of_week=0),
        ).status_code
        == 201
    )

    response = client.get("/employees/1/schedule")

    assert response.status_code == 200
    assert [schedule["day_of_week"] for schedule in response.json()] == [0, 2]


def test_schedule_can_be_updated(client):
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(day_of_week=0),
        ).status_code
        == 201
    )

    response = client.put(
        "/employees/1/schedule",
        json=make_schedule(
            day_of_week=0,
            start_time="08:00:00",
            end_time="16:00:00",
        ),
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "08:00:00"
    assert response.json()["end_time"] == "16:00:00"


def test_duplicate_schedule_is_rejected(client):
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(day_of_week=0),
        ).status_code
        == 201
    )

    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Schedule for this day already exists"}


def test_invalid_schedule_time_range_returns_422(client):
    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(
            day_of_week=0,
            start_time="17:00:00",
            end_time="09:00:00",
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]


def create_friday_appointment(client, start_at="2026-09-25T10:00:00+02:00"):
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(day_of_week=4),
        ).status_code
        == 201
    )
    response = client.post(
        "/appointments",
        json={
            "employee_id": 1,
            "service_id": 1,
            "start_at": start_at,
            "client_name": "Jan Kowalski",
            "client_email": "jan@example.com",
            "client_phone": "123456789",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("status", ["pending", "confirmed"])
@pytest.mark.parametrize("target_date", ["2026-09-25", "2026-10-02"])
@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [("10:15:00", "17:00:00"), ("09:00:00", "10:30:00")],
)
def test_schedule_change_rejects_active_appointments_outside_new_hours(
    client, status, target_date, start_time, end_time
):
    appointment = create_friday_appointment(client, f"{target_date}T10:00:00+02:00")
    if status == "confirmed":
        assert (
            client.patch(
                f"/appointments/{appointment['id']}/status", json={"status": status}
            ).status_code
            == 200
        )

    response = client.put(
        "/employees/1/schedule",
        json=make_schedule(4, start_time, end_time),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Schedule change would leave an active appointment "
        "outside employee working hours"
    }
    unchanged = client.get("/employees/1/schedule").json()[0]
    assert unchanged["start_time"] == "09:00:00"
    assert unchanged["end_time"] == "17:00:00"


def test_schedule_can_match_appointment_boundaries(client):
    create_friday_appointment(client)

    response = client.put(
        "/employees/1/schedule",
        json=make_schedule(4, "10:00:00", "10:45:00"),
    )

    assert response.status_code == 200


@pytest.mark.parametrize("status", ["cancelled", "completed"])
def test_schedule_change_ignores_terminal_appointments(client, status):
    appointment = create_friday_appointment(client)
    if status == "completed":
        assert (
            client.patch(
                f"/appointments/{appointment['id']}/status",
                json={"status": "confirmed"},
            ).status_code
            == 200
        )
    assert (
        client.patch(
            f"/appointments/{appointment['id']}/status", json={"status": status}
        ).status_code
        == 200
    )

    response = client.put(
        "/employees/1/schedule", json=make_schedule(4, end_time="10:00:00")
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("current_time", "expected_status"),
    [("2026-09-25T08:15:00Z", 409), ("2026-09-25T08:45:00Z", 200)],
)
def test_schedule_change_protects_in_progress_but_not_ended_appointments(
    client, monkeypatch, current_time, expected_status
):
    create_friday_appointment(client)
    monkeypatch.setattr(
        "app.routers.schedules.utc_now",
        lambda: datetime.fromisoformat(current_time),
    )

    response = client.put(
        "/employees/1/schedule", json=make_schedule(4, end_time="10:30:00")
    )

    assert response.status_code == expected_status


def test_schedule_change_ignores_appointments_on_other_weekdays(client):
    create_friday_appointment(client)
    assert (
        client.post("/employees/1/schedule", json=make_schedule(0)).status_code == 201
    )

    response = client.put(
        "/employees/1/schedule", json=make_schedule(0, end_time="10:00:00")
    )

    assert response.status_code == 200


def test_schedule_change_ignores_other_employee_appointments(client):
    create_friday_appointment(client)
    assert (
        client.post("/employees/2/schedule", json=make_schedule(4)).status_code == 201
    )

    response = client.put(
        "/employees/2/schedule", json=make_schedule(4, end_time="10:00:00")
    )

    assert response.status_code == 200


def test_schedule_change_uses_salon_weekday_instead_of_utc_weekday(client):
    assert (
        client.post(
            "/employees/1/schedule",
            json=make_schedule(0, "00:00:00", "03:00:00"),
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/appointments",
            json={
                "employee_id": 1,
                "service_id": 1,
                "start_at": "2026-09-28T00:15:00+02:00",
                "client_name": "Jan Kowalski",
                "client_email": "jan@example.com",
                "client_phone": "123456789",
            },
        ).status_code
        == 201
    )

    response = client.put(
        "/employees/1/schedule",
        json=make_schedule(0, "00:00:00", "00:30:00"),
    )

    assert response.status_code == 409


def test_updating_missing_schedule_returns_404(client):
    response = client.put("/employees/1/schedule", json=make_schedule(0))

    assert response.status_code == 404
    assert response.json() == {"detail": "Schedule for this day not found"}


def test_updating_schedule_for_missing_employee_returns_404(client):
    response = client.put("/employees/999/schedule", json=make_schedule(0))

    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}
