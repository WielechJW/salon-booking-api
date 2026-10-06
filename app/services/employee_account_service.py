from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import EmployeeModel
from app.models.user import UserModel
from app.services.errors import DomainConflictError, DomainNotFoundError


def assign_employee_account(
    *, database_session: Session, employee_id: int, user_id: int
) -> None:
    user = database_session.scalar(
        select(UserModel)
        .where(UserModel.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None:
        raise DomainNotFoundError("User not found")
    employee = database_session.scalar(
        select(EmployeeModel)
        .where(EmployeeModel.id == employee_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if employee is None:
        raise DomainNotFoundError("Employee not found")
    if not user.is_active or user.role == "ADMIN":
        raise DomainConflictError("Account cannot be assigned to an employee")
    if employee.user_id is not None and employee.user_id != user_id:
        raise DomainConflictError("Employee already has an account")
    existing = database_session.scalar(
        select(EmployeeModel.id).where(
            EmployeeModel.user_id == user_id, EmployeeModel.id != employee_id
        )
    )
    if existing is not None:
        raise DomainConflictError("Account is already assigned to another employee")
    employee.user_id = user_id
    user.role = "EMPLOYEE"
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise DomainConflictError("Employee account assignment conflicts") from error
