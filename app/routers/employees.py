from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.schemas.employee import Employee, EmployeeResponse


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeResponse])
def get_employees(database_session: Session = Depends(get_db)):
    query = select(EmployeeModel).order_by(EmployeeModel.id)
    return database_session.scalars(query).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


@router.post("", status_code=201, response_model=EmployeeResponse)
def create_employee(
    employee: Employee,
    database_session: Session = Depends(get_db),
):
    new_employee = EmployeeModel(name=employee.name)

    database_session.add(new_employee)
    database_session.commit()
    database_session.refresh(new_employee)

    return new_employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    updated_employee: Employee,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.name = updated_employee.name
    database_session.commit()
    database_session.refresh(employee)

    return employee


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    appointment_id = database_session.scalar(
        select(AppointmentModel.id)
        .where(AppointmentModel.employee_id == employee_id)
        .limit(1)
    )

    if appointment_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Employee has appointments and cannot be deleted",
        )

    database_session.delete(employee)
    database_session.commit()

    return {"message": "Employee deleted successfully"}
