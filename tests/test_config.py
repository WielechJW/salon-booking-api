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
