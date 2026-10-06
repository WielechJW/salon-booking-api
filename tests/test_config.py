import pytest
from pydantic import ValidationError

from app.config import Settings
from app.database import create_database_engine


def test_settings_use_sqlite_by_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./salon.db"


def test_settings_read_database_url_from_environment(monkeypatch):
    database_url = "postgresql+psycopg://salon:salon@db:5432/salon"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings(_env_file=None)

    assert settings.database_url == database_url


def test_settings_use_warsaw_timezone_by_default(monkeypatch):
    monkeypatch.delenv("SALON_TIMEZONE", raising=False)

    settings = Settings(_env_file=None)

    assert settings.salon_timezone == "Europe/Warsaw"


def test_settings_reject_unknown_timezone(monkeypatch):
    monkeypatch.setenv("SALON_TIMEZONE", "Invalid/Timezone")

    with pytest.raises(ValidationError, match="Unknown IANA timezone"):
        Settings(_env_file=None)


def test_sqlite_engine_enables_foreign_keys(tmp_path):
    database_path = tmp_path / "foreign-keys.db"
    engine = create_database_engine(f"sqlite:///{database_path}")

    try:
        with engine.connect() as connection:
            foreign_keys_enabled = connection.exec_driver_sql(
                "PRAGMA foreign_keys"
            ).scalar_one()
    finally:
        engine.dispose()

    assert foreign_keys_enabled == 1


def test_default_jwt_keys_are_random_and_hidden(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    first = Settings(_env_file=None)
    second = Settings(_env_file=None)
    assert first.jwt_secret_key != second.jwt_secret_key
    assert len(first.jwt_secret_key.get_secret_value()) >= 32
    assert first.jwt_secret_key.get_secret_value() not in repr(first)


def test_short_jwt_key_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("minutes", [0, -1, 1441])
def test_invalid_token_lifetime_is_rejected(minutes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, access_token_expire_minutes=minutes)
