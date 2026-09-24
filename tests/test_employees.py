import pytest
from fastapi import HTTPException

from app.routers.employees import (
    create_employee,
    delete_employee,
    get_employee,
    get_employees,
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
