from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models.appointment import AppointmentModel
from app.security import create_access_token
from app.timezone import as_utc


@pytest.fixture
def add_appointment(database_session):
    def add(start_at, *, employee_id=1, client_id=2, status="pending"):
        start = as_utc(datetime.fromisoformat(start_at))
        appointment = AppointmentModel(
            employee_id=employee_id,
            service_id=1,
            client_id=client_id,
            start_at=start,
            end_at=start + timedelta(minutes=15),
            duration_minutes=15,
            price=80,
            status=status,
            client_name="Jan Kowalski",
            client_email="jan@example.com",
            client_phone="123456789",
        )
        database_session.add(appointment)
        database_session.commit()
        return appointment.id

    return add


def user_headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.mark.parametrize("path", ["/appointments", "/users/me/appointments"])
def test_pagination_has_stable_order_and_filtered_total(
    anonymous_client, add_appointment, path
):
    later = add_appointment("2026-09-25T11:00:00+02:00")
    first = add_appointment("2026-09-25T10:00:00+02:00", employee_id=2)
    second = add_appointment("2026-09-25T10:00:00+02:00")
    add_appointment("2026-09-25T09:00:00+02:00", client_id=3)
    headers = user_headers(2)
    response = anonymous_client.get(
        path, headers=headers, params={"limit": 1, "offset": 1}
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [second]
    assert response.headers["X-Total-Count"] == "3"
    assert response.headers["X-Limit"] == "1"
    assert response.headers["X-Offset"] == "1"
    pages = [
        anonymous_client.get(
            path, headers=headers, params={"limit": 1, "offset": offset}
        ).json()[0]["id"]
        for offset in range(3)
    ]
    assert pages == [first, second, later]
    beyond = anonymous_client.get(path, headers=headers, params={"offset": 3})
    assert beyond.json() == []
    assert beyond.headers["X-Total-Count"] == "3"


def test_default_page_size_is_bounded(client, add_appointment):
    start = datetime.fromisoformat("2026-09-25T09:00:00+02:00")
    for index in range(55):
        add_appointment((start + timedelta(minutes=15 * index)).isoformat())
    response = client.get("/appointments")
    assert len(response.json()) == 50
    assert response.headers["X-Total-Count"] == "55"
    assert response.headers["X-Limit"] == "50"
    assert response.headers["X-Offset"] == "0"
    assert len(client.get("/appointments", params={"offset": 50}).json()) == 5


@pytest.mark.parametrize("path", ["/appointments", "/users/me/appointments"])
def test_date_status_and_employee_filters_combine(
    anonymous_client, add_appointment, path
):
    expected = add_appointment("2026-09-25T10:00:00+02:00", status="confirmed")
    add_appointment("2026-09-25T11:00:00+02:00", status="pending")
    add_appointment("2026-09-25T12:00:00+02:00", employee_id=2, status="confirmed")
    add_appointment("2026-09-26T10:00:00+02:00", status="confirmed")
    add_appointment("2026-09-25T13:00:00+02:00", client_id=3, status="confirmed")
    response = anonymous_client.get(
        path,
        headers=user_headers(2),
        params={
            "employee_id": 1,
            "status": "confirmed",
            "date_from": "2026-09-25",
            "date_to": "2026-09-25",
            "limit": 1,
        },
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [expected]
    assert response.headers["X-Total-Count"] == "1"


@pytest.mark.parametrize(
    ("target_date", "before", "first", "last", "after"),
    [
        (
            "2026-10-25",
            "2026-10-24T23:59:59+02:00",
            "2026-10-25T00:00:00+02:00",
            "2026-10-25T23:59:59+01:00",
            "2026-10-26T00:00:00+01:00",
        ),
        (
            "2027-03-28",
            "2027-03-27T23:59:59+01:00",
            "2027-03-28T00:00:00+01:00",
            "2027-03-28T23:59:59+02:00",
            "2027-03-29T00:00:00+02:00",
        ),
    ],
)
def test_date_range_uses_local_day_boundaries_including_dst(
    client, add_appointment, target_date, before, first, last, after
):
    add_appointment(before)
    expected = [add_appointment(first), add_appointment(last)]
    add_appointment(after)
    response = client.get(
        "/appointments",
        params={
            "date_from": target_date,
            "date_to": target_date,
        },
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == expected
    assert response.headers["X-Total-Count"] == "2"


def test_date_range_respects_configured_timezone(client, add_appointment, monkeypatch):
    monkeypatch.setattr(
        "app.services.appointment_list_service.get_salon_timezone",
        lambda: ZoneInfo("Asia/Tokyo"),
    )
    expected = add_appointment("2026-09-25T00:00:00+09:00")
    add_appointment("2026-09-26T00:00:00+09:00")
    response = client.get(
        "/appointments",
        params={
            "date_from": "2026-09-25",
            "date_to": "2026-09-25",
        },
    )
    assert [item["id"] for item in response.json()] == [expected]


def test_date_bounds_can_be_used_independently(client, add_appointment):
    first = add_appointment("2026-09-24T10:00:00+02:00")
    second = add_appointment("2026-09-25T10:00:00+02:00")
    third = add_appointment("2026-09-26T10:00:00+02:00")
    assert [
        item["id"]
        for item in client.get(
            "/appointments", params={"date_from": "2026-09-25"}
        ).json()
    ] == [second, third]
    assert [
        item["id"]
        for item in client.get("/appointments", params={"date_to": "2026-09-25"}).json()
    ] == [first, second]


@pytest.mark.parametrize("path", ["/appointments", "/users/me/appointments"])
@pytest.mark.parametrize(
    "params",
    [
        {"date_from": "2026-09-26", "date_to": "2026-09-25"},
        {"date_from": "invalid"},
        {"date_to": "2026-02-30"},
        {"date_to": "9999-12-31"},
        {"date_from": "0001-01-01"},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": "not-an-integer"},
        {"offset": 9223372036854775808},
        {"employee_id": 0},
        {"employee_id": 2147483648},
        {"status": "unknown"},
        {"client_id": 3},
    ],
)
def test_invalid_list_parameters_return_422(client, path, params):
    assert client.get(path, params=params).status_code == 422


@pytest.mark.parametrize(
    ("user_id", "expected_count"), [(1, 5), (2, 2), (4, 3), (5, 2)]
)
def test_pagination_and_total_preserve_role_scope(
    anonymous_client, add_appointment, user_id, expected_count
):
    add_appointment("2026-09-25T09:00:00+02:00", employee_id=1, client_id=2)
    add_appointment("2026-09-25T10:00:00+02:00", employee_id=1, client_id=3)
    add_appointment("2026-09-25T11:00:00+02:00", employee_id=2, client_id=2)
    add_appointment("2026-09-25T12:00:00+02:00", employee_id=2, client_id=3)
    add_appointment("2026-09-25T13:00:00+02:00", employee_id=1, client_id=None)
    response = anonymous_client.get(
        "/appointments",
        headers=user_headers(user_id),
        params={
            "date_from": "2026-09-25",
            "date_to": "2026-09-25",
            "limit": 1,
            "offset": 1,
        },
    )
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == str(expected_count)
    item = response.json()[0]
    if user_id == 2:
        assert item["client_id"] == 2
    if user_id in (4, 5):
        assert item["employee_id"] == user_id - 3
        other_employee = 2 if user_id == 4 else 1
        response = anonymous_client.get(
            "/appointments",
            headers=user_headers(user_id),
            params={
                "employee_id": other_employee,
                "limit": 1,
            },
        )
        assert response.json() == []
        assert response.headers["X-Total-Count"] == "0"


def test_my_history_is_owned_even_for_employee_role(anonymous_client, add_appointment):
    expected = add_appointment("2026-09-25T09:00:00+02:00", employee_id=2, client_id=4)
    add_appointment("2026-09-25T10:00:00+02:00", employee_id=1, client_id=2)
    response = anonymous_client.get(
        "/users/me/appointments", headers=user_headers(4), params={"employee_id": 2}
    )
    assert [item["id"] for item in response.json()] == [expected]
    assert response.headers["X-Total-Count"] == "1"
