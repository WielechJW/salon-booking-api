import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

import app.models
from app.database import Base, create_database_engine, get_db
from app.main import app
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.service import ServiceModel

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FIXTURES = {"client", "database_session"}


def pytest_collection_modifyitems(items):
    for item in items:
        marker = (
            pytest.mark.integration
            if DATABASE_FIXTURES.intersection(item.fixturenames)
            else pytest.mark.unit
        )
        item.add_marker(marker)


@pytest.fixture(autouse=True)
def freeze_current_time(monkeypatch):
    monkeypatch.setattr(
        "app.routers.appointments.utc_now",
        lambda: datetime(2026, 9, 24, 12, tzinfo=timezone.utc),
    )


def validate_test_database_url(database_url: str) -> str:
    database_name = make_url(database_url).database or ""

    if "test" not in database_name.lower():
        raise RuntimeError("Test database name must contain 'test'")

    return database_url


def migrate_database(database_url: str) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(PROJECT_ROOT / "migrations"),
    )
    alembic_config.attributes["database_url"] = database_url
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def test_database_url(tmp_path_factory) -> str:
    if TEST_DATABASE_URL is not None:
        return validate_test_database_url(TEST_DATABASE_URL)

    database_path = tmp_path_factory.mktemp("database") / "test.db"
    database_url = f"sqlite:///{database_path}"
    migrate_database(database_url)
    return database_url


def clear_database(test_engine) -> None:
    if test_engine.dialect.name == "postgresql":
        preparer = test_engine.dialect.identifier_preparer
        table_names = ", ".join(
            preparer.quote(table.name) for table in Base.metadata.sorted_tables
        )

        with test_engine.begin() as connection:
            connection.exec_driver_sql(
                f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"
            )
        return

    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def database_session(test_database_url):
    test_engine = create_database_engine(test_database_url)
    clear_database(test_engine)

    with Session(test_engine) as session:
        employees = [
            EmployeeModel(name="Anna Kowalska"),
            EmployeeModel(name="Bartek Nowak"),
        ]
        services = [
            ServiceModel(
                name="Strzyżenie męskie",
                description="Profesjonalne strzyżenie męskie",
                duration_minutes=45,
                price=Decimal("80.00"),
            ),
            ServiceModel(
                name="Strzyżenie damskie",
                description="Profesjonalne strzyżenie damskie",
                duration_minutes=60,
                price=Decimal("120.00"),
            ),
        ]

        session.add_all([*employees, *services])
        session.flush()
        session.add_all(
            [
                EmployeeServiceModel(
                    employee_id=employees[0].id,
                    service_id=services[0].id,
                ),
                EmployeeServiceModel(
                    employee_id=employees[0].id,
                    service_id=services[1].id,
                ),
            ]
        )
        session.commit()

        yield session

    test_engine.dispose()


@pytest.fixture
def client(database_session):
    def override_get_db():
        yield database_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
