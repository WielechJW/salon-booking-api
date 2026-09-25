from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.schemas.employee import Employee, EmployeeResponse

from app.models.employee_service import EmployeeServiceModel
from app.models.service import ServiceModel
from app.schemas.service import ServiceResponse


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

@router.post("/{employee_id}/services/{service_id}", status_code=201)
def assign_service_to_employee(
    employee_id: int,
    service_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    service = database_session.get(ServiceModel, service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    assignment = database_session.get(
        EmployeeServiceModel,
        (employee_id, service_id),
    )

    if assignment is not None:
        raise HTTPException(
            status_code=409,
            detail="Service is already assigned to this employee",
        )

    new_assignment = EmployeeServiceModel(
        employee_id=employee_id,
        service_id=service_id,
    )

    database_session.add(new_assignment)
    database_session.commit()

    return {"message": "Service assigned to employee"}

@router.get(
    "/{employee_id}/services",
    response_model=list[ServiceResponse],
)
def get_employee_services(
    employee_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    query = (
        select(ServiceModel)
        .join(
            EmployeeServiceModel,
            ServiceModel.id == EmployeeServiceModel.service_id,
        )
        .where(EmployeeServiceModel.employee_id == employee_id)
        .order_by(ServiceModel.id)
    )

    return database_session.scalars(query).all()

@router.delete("/{employee_id}/services/{service_id}")
def remove_service_from_employee(
    employee_id: int,
    service_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    service = database_session.get(ServiceModel, service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    assignment = database_session.get(
        EmployeeServiceModel,
        (employee_id, service_id),
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Service is not assigned to this employee",
        )

    database_session.delete(assignment)
    database_session.commit()

    return {"message": "Service removed from employee"}