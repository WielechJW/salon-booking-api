import os
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.models.employee_service import EmployeeServiceModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTGRES_TESTS_ENABLED = os.getenv(
    "TEST_DATABASE_URL",
    "",
).startswith("postgresql")


def get_alembic_head() -> str:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(PROJECT_ROOT / "migrations"),
    )
    return ScriptDirectory.from_config(alembic_config).get_current_head()


def test_database_schema_is_created_by_latest_migration(database_session):
    current_revision = database_session.scalar(
        text("SELECT version_num FROM alembic_version")
    )

    assert current_revision == get_alembic_head()


def test_database_enforces_foreign_keys(database_session):
    database_session.add(
        EmployeeServiceModel(
            employee_id=999_999,
            service_id=1,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()

    database_session.rollback()


@pytest.mark.postgres
@pytest.mark.skipif(
    not POSTGRES_TESTS_ENABLED,
    reason="PostgreSQL-specific column type",
)
def test_postgresql_stores_appointment_timestamps_with_timezone(database_session):
    columns = {
        column["name"]: column
        for column in inspect(database_session.get_bind()).get_columns("appointments")
    }

    assert columns["start_at"]["type"].timezone is True
    assert columns["end_at"]["type"].timezone is True
