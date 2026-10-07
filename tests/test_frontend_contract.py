import pytest

from app.config import get_settings
from app.security import create_access_token


@pytest.mark.parametrize(("user_id", "employee_id"), [(1, None), (2, None), (4, 1)])
def test_profile_returns_only_own_employee_id(anonymous_client, user_id, employee_id):
    response = anonymous_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {create_access_token(user_id)}"},
    )
    assert response.status_code == 200
    assert response.json()["employee_id"] == employee_id
    assert "password_hash" not in response.json()


def test_public_salon_info_uses_configured_timezone(anonymous_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "salon_timezone", "Europe/London")
    response = anonymous_client.get("/salon")
    assert response.status_code == 200
    assert response.json() == {"timezone": "Europe/London"}
