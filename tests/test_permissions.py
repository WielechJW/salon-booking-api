import pytest

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.user import UserModel
from app.security import create_access_token


def headers_for(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def booking_payload(**changes):
    return {
        "employee_id": 1,
        "service_id": 1,
        "start_at": "2026-09-25T10:00:00+02:00",
        "client_name": "Jan Kowalski",
        "client_email": "jan@example.com",
        "client_phone": "123456789",
        **changes,
    }


@pytest.fixture
def owned_appointment(client, anonymous_client):
    response = client.post(
        "/employees/1/schedule",
        json={"day_of_week": 4, "start_time": "09:00:00", "end_time": "18:00:00"},
    )
    assert response.status_code == 201
    response = anonymous_client.post(
        "/appointments", json=booking_payload(), headers=headers_for(2)
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/appointments", None),
        ("get", "/appointments/1", None),
        ("post", "/appointments", booking_payload()),
        ("patch", "/appointments/1/status", {"status": "cancelled"}),
        ("get", "/users/me", None),
        ("get", "/users/me/appointments", None),
        ("post", "/services", {}),
        ("put", "/services/1", {}),
        ("delete", "/services/1", None),
        ("post", "/employees", {}),
        ("put", "/employees/1", {}),
        ("delete", "/employees/1", None),
        ("post", "/employees/1/services/1", None),
        ("delete", "/employees/1/services/1", None),
        ("get", "/employees/1/schedule", None),
        ("post", "/employees/1/schedule", {}),
        ("put", "/employees/1/schedule", {}),
        ("get", "/employees/1/time-off", None),
        ("post", "/employees/1/time-off", {}),
        ("put", "/employees/1/time-off/1", {}),
        ("delete", "/employees/1/time-off/1", None),
        ("put", "/employees/1/account", {"user_id": 3}),
    ],
)
def test_protected_endpoints_require_authentication(
    anonymous_client, method, path, payload
):
    response = anonymous_client.request(method, path, json=payload)
    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/services",
        "/employees",
        "/employees/1/services",
        "/employees/1/availability?date=2026-09-25&service_id=1",
    ],
)
def test_booking_catalog_is_public(anonymous_client, path):
    response = anonymous_client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize("user_id", [2, 4])
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/services", {}),
        ("put", "/services/1", {}),
        ("delete", "/services/1", None),
        ("post", "/employees", {}),
        ("put", "/employees/1", {}),
        ("delete", "/employees/1", None),
        ("post", "/employees/1/services/1", None),
        ("delete", "/employees/1/services/1", None),
        ("put", "/employees/1/account", {"user_id": 3}),
    ],
)
def test_only_admin_can_manage_catalog_and_accounts(
    anonymous_client, user_id, method, path, payload
):
    response = anonymous_client.request(
        method, path, json=payload, headers=headers_for(user_id)
    )
    assert response.status_code == 403


def test_appointment_owner_cannot_be_spoofed(anonymous_client, owned_appointment):
    payload = booking_payload(client_id=3, start_at="2026-09-25T11:00:00+02:00")
    response = anonymous_client.post(
        "/appointments", json=payload, headers=headers_for(2)
    )
    assert response.status_code == 403
    assert owned_appointment["client_id"] == 2


def test_client_can_only_list_own_appointments(
    anonymous_client, client, owned_appointment
):
    other = client.post(
        "/appointments",
        json=booking_payload(client_id=3, start_at="2026-09-25T11:00:00+02:00"),
    )
    assert other.status_code == 201
    for path in ("/appointments", "/users/me/appointments"):
        response = anonymous_client.get(path, headers=headers_for(2))
        assert [item["id"] for item in response.json()] == [owned_appointment["id"]]
    assert len(client.get("/appointments").json()) == 2
    assert client.get("/users/me/appointments").json() == []


@pytest.mark.parametrize("user_id", [3, 5])
def test_other_client_and_employee_cannot_access_or_cancel_appointment(
    anonymous_client, owned_appointment, user_id
):
    path = f"/appointments/{owned_appointment['id']}"
    assert anonymous_client.get(path, headers=headers_for(user_id)).status_code == 404
    assert (
        anonymous_client.patch(
            f"{path}/status", json={"status": "cancelled"}, headers=headers_for(user_id)
        ).status_code
        == 404
    )
    assert (
        anonymous_client.get(path, headers=headers_for(2)).json()["status"] == "pending"
    )


@pytest.mark.parametrize("status", ["pending", "confirmed", "completed"])
def test_client_can_only_cancel_own_appointment(
    anonymous_client, owned_appointment, status
):
    response = anonymous_client.patch(
        f"/appointments/{owned_appointment['id']}/status",
        json={"status": status},
        headers=headers_for(2),
    )
    assert response.status_code == 403


def test_client_can_cancel_own_appointment(anonymous_client, owned_appointment):
    response = anonymous_client.patch(
        f"/appointments/{owned_appointment['id']}/status",
        json={"status": "cancelled"},
        headers=headers_for(2),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_employee_can_view_and_change_status_in_own_calendar(
    anonymous_client, owned_appointment
):
    response = anonymous_client.get("/appointments", headers=headers_for(4))
    assert [item["id"] for item in response.json()] == [owned_appointment["id"]]
    assert anonymous_client.get("/appointments", headers=headers_for(5)).json() == []
    response = anonymous_client.patch(
        f"/appointments/{owned_appointment['id']}/status",
        json={"status": "confirmed"},
        headers=headers_for(4),
    )
    assert response.status_code == 200


@pytest.mark.parametrize("user_id", [2, 5])
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/employees/1/schedule", None),
        ("post", "/employees/1/schedule", {}),
        ("put", "/employees/1/schedule", {}),
        ("get", "/employees/1/time-off", None),
        ("post", "/employees/1/time-off", {}),
        ("put", "/employees/1/time-off/1", {}),
        ("delete", "/employees/1/time-off/1", None),
    ],
)
def test_clients_and_other_employees_cannot_access_calendar(
    anonymous_client, user_id, method, path, payload
):
    response = anonymous_client.request(
        method, path, json=payload, headers=headers_for(user_id)
    )
    assert response.status_code == 403


def test_employee_can_manage_own_schedule_and_time_off(anonymous_client):
    headers = headers_for(4)
    schedule = {"day_of_week": 4, "start_time": "09:00:00", "end_time": "17:00:00"}
    assert (
        anonymous_client.post(
            "/employees/1/schedule", json=schedule, headers=headers
        ).status_code
        == 201
    )
    schedule["end_time"] = "18:00:00"
    assert (
        anonymous_client.put(
            "/employees/1/schedule", json=schedule, headers=headers
        ).status_code
        == 200
    )
    assert (
        len(anonymous_client.get("/employees/1/schedule", headers=headers).json()) == 1
    )
    time_off = {
        "start_at": "2026-09-25T12:00:00+02:00",
        "end_at": "2026-09-25T13:00:00+02:00",
        "reason": "Lunch break",
    }
    response = anonymous_client.post(
        "/employees/1/time-off", json=time_off, headers=headers
    )
    assert response.status_code == 201
    path = f"/employees/1/time-off/{response.json()['id']}"
    time_off["reason"] = "Training"
    assert anonymous_client.put(path, json=time_off, headers=headers).status_code == 200
    assert anonymous_client.delete(path, headers=headers).status_code == 200


def test_admin_can_link_registered_account_to_employee(client, database_session):
    created = client.post("/employees", json={"name": "New Employee"}).json()
    response = client.put(f"/employees/{created['id']}/account", json={"user_id": 3})
    assert response.status_code == 200
    assert database_session.get(EmployeeModel, created["id"]).user_id == 3
    assert database_session.get(UserModel, 3).role == "EMPLOYEE"
    assert (
        client.get(
            f"/employees/{created['id']}/schedule", headers=headers_for(3)
        ).status_code
        == 200
    )


@pytest.mark.parametrize("user_id", [1, 4, 99999])
def test_account_assignment_rejects_admin_duplicate_and_missing_user(client, user_id):
    created = client.post("/employees", json={"name": "New Employee"}).json()
    response = client.put(
        f"/employees/{created['id']}/account", json={"user_id": user_id}
    )
    assert response.status_code == (404 if user_id == 99999 else 409)


def test_account_assignment_cannot_replace_existing_account(client):
    assert client.put("/employees/1/account", json={"user_id": 3}).status_code == 409


def test_legacy_unowned_appointments_are_not_claimed_by_matching_email(
    client, anonymous_client, owned_appointment, database_session
):
    stored = database_session.get(AppointmentModel, owned_appointment["id"])
    stored.client_id = None
    database_session.commit()
    assert client.get(f"/appointments/{stored.id}").status_code == 200
    assert (
        anonymous_client.get("/users/me/appointments", headers=headers_for(2)).json()
        == []
    )
    assert (
        anonymous_client.get(
            f"/appointments/{stored.id}", headers=headers_for(2)
        ).status_code
        == 404
    )
