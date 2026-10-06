from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.database import create_database_engine


@pytest.mark.integration
def test_user_migration_preserves_legacy_data_without_claiming_ownership(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy-test.db'}"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "a4c8d12e7f90")
    engine = create_database_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO employees (id, name) VALUES (1, 'Anna')")
            )
            connection.execute(
                text(
                    "INSERT INTO services (id, name, description, duration_minutes, price) "
                    "VALUES (1, 'Haircut', 'Standard haircut', 45, 80.00)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO appointments "
                    "(id, employee_id, service_id, start_at, end_at, duration_minutes, "
                    "price, client_name, client_email, client_phone, status) "
                    "VALUES (1, 1, 1, '2026-09-25 08:00:00', '2026-09-25 08:45:00', "
                    "45, 80.00, 'Jan Kowalski', 'jan@example.com', '123456789', 'pending')"
                )
            )
        command.upgrade(config, "head")
        command.check(config)
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT client_id, client_email, price FROM appointments WHERE id = 1"
                )
            ).one()
            assert row == (None, "jan@example.com", 80)
            assert (
                connection.scalar(text("SELECT user_id FROM employees WHERE id = 1"))
                is None
            )
            assert connection.scalar(text("SELECT COUNT(*) FROM users")) == 0
        command.downgrade(config, "a4c8d12e7f90")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT COUNT(*) FROM appointments")) == 1
        command.upgrade(config, "head")
    finally:
        engine.dispose()
