import pytest
from fastapi import HTTPException

from app.routers.employees import (
    assign_service_to_employee,
    create_employee,
    delete_employee,
    get_employee,
    get_employee_services,
    get_employees,
    remove_service_from_employee,
    update_employee,
)
from app.schemas.employee import Employee


def test_employee_crud_uses_database(database_session):
    created = create_employee(Employee(name="Kamil Wiśniewski"), database_session)

    assert created.id is not None
    assert get_employee(created.id, database_session).name == "Kamil Wiśniewski"
    assert any(employee.id == created.id for employee in get_employees(database_session))

    updated = update_employee(
        created.id,
        Employee(name="Kamil Nowak"),
        database_session,
    )
    assert updated.name == "Kamil Nowak"

    assert delete_employee(created.id, database_session) == {
        "message": "Employee deleted successfully"
    }

    with pytest.raises(HTTPException) as error:
        get_employee(created.id, database_session)

    assert error.value.status_code == 404

def test_service_can_be_assigned_to_employee(database_session):
    result = assign_service_to_employee(2, 1, database_session)

    assert result == {"message": "Service assigned to employee"}
    assert [service.id for service in get_employee_services(2, database_session)] == [1]


def test_employee_services_are_returned(database_session):
    services = get_employee_services(1, database_session)

    assert [service.id for service in services] == [1, 2]


def test_service_can_be_removed_from_employee(database_session):
    result = remove_service_from_employee(1, 1, database_session)

    assert result == {"message": "Service removed from employee"}
    assert [service.id for service in get_employee_services(1, database_session)] == [2]
