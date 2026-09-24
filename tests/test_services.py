import pytest
from fastapi import HTTPException

from app.routers.services import (
    create_service,
    delete_service,
    get_service,
    get_services,
    update_service,
)
from app.schemas.service import Service


def test_service_crud_uses_database(database_session):
    created = create_service(
        Service(
            name="Modelowanie",
            description="Profesjonalne modelowanie włosów",
            duration_minutes=30,
            price=70,
        ),
        database_session,
    )

    assert created.id is not None
    assert get_service(created.id, database_session).name == "Modelowanie"
    assert any(service.id == created.id for service in get_services(database_session))

    updated = update_service(
        created.id,
        Service(
            name="Modelowanie premium",
            description="Rozszerzone modelowanie włosów",
            duration_minutes=45,
            price=100,
        ),
        database_session,
    )
    assert updated.name == "Modelowanie premium"

    assert delete_service(created.id, database_session) == {
        "message": "Service deleted successfully"
    }

    with pytest.raises(HTTPException) as error:
        get_service(created.id, database_session)

    assert error.value.status_code == 404
