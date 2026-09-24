from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models
from app.database import Base
from app.models.employee import EmployeeModel
from app.models.service import ServiceModel


@pytest.fixture
def database_session(tmp_path):
    database_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{database_path}")
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
            ]
        )
        session.commit()

        yield session

    test_engine.dispose()
