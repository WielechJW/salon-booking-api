import os
from decimal import Decimal

import pytest
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


def get_test_database_url(tmp_path) -> str:
    if TEST_DATABASE_URL is None:
        return f"sqlite:///{tmp_path / 'test.db'}"

    database_name = make_url(TEST_DATABASE_URL).database or ""

    if "test" not in database_name.lower():
        raise RuntimeError("Test database name must contain 'test'")

    return TEST_DATABASE_URL


@pytest.fixture
def database_session(tmp_path):
    database_url = get_test_database_url(tmp_path)
    test_engine = create_database_engine(database_url)

    if TEST_DATABASE_URL is None:
        Base.metadata.create_all(bind=test_engine)
    else:
        preparer = test_engine.dialect.identifier_preparer
        table_names = ", ".join(
            preparer.quote(table.name) for table in Base.metadata.sorted_tables
        )

        with test_engine.begin() as connection:
            connection.exec_driver_sql(
                f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"
            )

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
