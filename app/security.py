from datetime import datetime, timedelta
from functools import lru_cache

import jwt
from pwdlib import PasswordHash

from app.config import get_settings
from app.timezone import utc_now

password_hasher = PasswordHash.recommended()
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "salon-booking-api"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


@lru_cache
def get_dummy_password_hash() -> str:
    return hash_password("dummy-password-for-nonexistent-users")


def create_access_token(user_id: int, *, current_time: datetime | None = None) -> str:
    settings = get_settings()
    now = current_time if current_time is not None else utc_now()
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
            "iss": JWT_ISSUER,
            "type": "access",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        get_settings().jwt_secret_key.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        options={"require": ["sub", "exp", "iat", "iss"]},
    )
    subject = payload["sub"]
    if (
        payload.get("type") != "access"
        or not isinstance(subject, str)
        or not subject.isascii()
        or not subject.isdecimal()
        or len(subject) > 10
        or not 0 < int(subject) <= 2147483647
    ):
        raise jwt.InvalidTokenError("Invalid access token subject or type")
    return int(subject)
