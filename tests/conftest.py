from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models
from app.database import Base, get_db
from app.main import app
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.service import ServiceModel


@pytest.fixture
def database_session(tmp_path):
    database_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)

    with Session(test_engine) as session:
        session.add_all(
            [
                EmployeeModel(id=1, name="Anna Kowalska"),
                EmployeeModel(id=2, name="Bartek Nowak"),
                ServiceModel(
                    id=1,
                    name="Strzyżenie męskie",
                    description="Profesjonalne strzyżenie męskie",
                    duration_minutes=45,
                    price=Decimal("80.00"),
                ),
                ServiceModel(
                    id=2,
                    name="Strzyżenie damskie",
                    description="Profesjonalne strzyżenie damskie",
                    duration_minutes=60,
                    price=Decimal("120.00"),
                ),
                EmployeeServiceModel(employee_id=1, service_id=1),
                EmployeeServiceModel(employee_id=1, service_id=2),
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
