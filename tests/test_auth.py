from datetime import timedelta

import jwt
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.models.user import UserModel
from app.security import JWT_ALGORITHM, JWT_ISSUER, create_access_token, verify_password
from app.timezone import utc_now


def registration_payload(**changes):
    return {
        "email": "new@example.com",
        "password": "StrongPassword123!",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "+48123456789",
        **changes,
    }


def test_registration_hashes_password_and_creates_client(
    anonymous_client, database_session
):
    response = anonymous_client.post(
        "/auth/register",
        json=registration_payload(
            email="  NEW@EXAMPLE.COM  ", first_name=" Jan ", phone="+48 123-456-789"
        ),
    )

    assert response.status_code == 201
    user = response.json()
    assert user["role"] == "CLIENT"
    assert user["email"] == "new@example.com"
    assert user["first_name"] == "Jan"
    assert user["phone"] == "+48123456789"
    assert "password" not in user and "password_hash" not in user
    stored = database_session.get(UserModel, user["id"])
    assert stored.password_hash.startswith("$argon2id$")
    assert verify_password("StrongPassword123!", stored.password_hash)


def test_duplicate_email_is_case_insensitive(anonymous_client):
    response = anonymous_client.post(
        "/auth/register", json=registration_payload(email=" JAN@EXAMPLE.COM ")
    )
    assert response.status_code == 409


@pytest.mark.parametrize("field", ["role", "is_active", "id", "password_hash"])
def test_registration_cannot_set_privileged_fields(anonymous_client, field):
    payload = registration_payload()
    payload[field] = "ADMIN"
    response = anonymous_client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "invalid"),
        ("password", "short"),
        ("password", "x" * 129),
        ("first_name", "  "),
        ("last_name", "  "),
        ("phone", "abcdefg"),
    ],
)
def test_registration_validates_profile(anonymous_client, field, value):
    response = anonymous_client.post(
        "/auth/register", json=registration_payload(**{field: value})
    )
    assert response.status_code == 422


def test_login_and_me_use_real_bearer_token(anonymous_client):
    response = anonymous_client.post(
        "/auth/login",
        data={"username": " JAN@EXAMPLE.COM ", "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    response = anonymous_client.get(
        "/users/me", headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["role"] == "CLIENT"
    assert "password_hash" not in response.json()


@pytest.mark.parametrize(
    ("email", "password"),
    [("jan@example.com", "wrong"), ("missing@example.com", "TestPassword123!")],
)
def test_login_rejects_invalid_credentials(anonymous_client, email, password):
    response = anonymous_client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == "Invalid or expired credentials"


def test_inactive_user_cannot_login_or_use_existing_token(
    anonymous_client, database_session
):
    token = create_access_token(2)
    database_session.get(UserModel, 2).is_active = False
    database_session.commit()
    assert (
        anonymous_client.post(
            "/auth/login",
            data={"username": "jan@example.com", "password": "TestPassword123!"},
        ).status_code
        == 401
    )
    assert (
        anonymous_client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize("token", ["invalid", "", "a.b.c"])
def test_malformed_tokens_return_401(anonymous_client, token):
    response = anonymous_client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_expired_token_is_rejected(anonymous_client):
    token = create_access_token(2, current_time=utc_now() - timedelta(days=2))
    response = anonymous_client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "changes",
    [
        {"sub": "not-an-id"},
        {"sub": "0"},
        {"sub": "999999999999999"},
        {"sub": "999999"},
        {"type": "refresh"},
        {"iss": "other-app"},
    ],
)
def test_invalid_token_claims_are_rejected(anonymous_client, changes):
    payload = {
        "sub": "2",
        "iat": utc_now(),
        "exp": utc_now() + timedelta(minutes=5),
        "iss": JWT_ISSUER,
        "type": "access",
        **changes,
    }
    token = jwt.encode(
        payload,
        get_settings().jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    response = anonymous_client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("missing_claim", ["sub", "exp", "iat", "iss"])
def test_token_must_include_required_claims(anonymous_client, missing_claim):
    payload = {
        "sub": "2",
        "iat": utc_now(),
        "exp": utc_now() + timedelta(minutes=5),
        "iss": JWT_ISSUER,
        "type": "access",
    }
    payload.pop(missing_claim)
    token = jwt.encode(
        payload,
        get_settings().jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    assert (
        anonymous_client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize("algorithm", ["HS256", "HS384"])
def test_invalid_signature_or_algorithm_is_rejected(
    anonymous_client, algorithm, monkeypatch
):
    signing_key = "a" * 64
    monkeypatch.setattr(get_settings(), "jwt_secret_key", SecretStr(signing_key))
    token = jwt.encode(
        {
            "sub": "2",
            "iat": utc_now(),
            "exp": utc_now() + timedelta(minutes=5),
            "iss": JWT_ISSUER,
            "type": "access",
        },
        signing_key if algorithm == "HS384" else "b" * 64,
        algorithm=algorithm,
    )
    assert (
        anonymous_client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_roles_are_loaded_from_database_for_existing_tokens(
    anonymous_client, database_session
):
    headers = {"Authorization": f"Bearer {create_access_token(1)}"}
    database_session.get(UserModel, 1).role = "CLIENT"
    database_session.commit()
    response = anonymous_client.delete("/services/1", headers=headers)
    assert response.status_code == 403


def test_email_unique_constraint_is_enforced(database_session):
    user = database_session.scalar(select(UserModel).where(UserModel.id == 2))
    database_session.add(
        UserModel(
            email=user.email,
            password_hash=user.password_hash,
            first_name="Other",
            last_name="User",
            phone="123456789",
            role="CLIENT",
            is_active=True,
        )
    )
    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()
