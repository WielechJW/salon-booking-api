from fastapi import APIRouter, HTTPException 
import app.data as data
from app.schemas.employee import Employee

router = APIRouter(prefix="/employees", tags=["employees"])

def get_next_employee_id():
    if not data.employees:
        return 1

    return max(employee["id"] for employee in data.employees) + 1


@router.get("")
def get_employees():
    return data.employees

@router.get("/{employee_id}")
def get_employee(employee_id: int):
    for employee in data.employees:
        if employee["id"] == employee_id:
            return employee

    raise HTTPException(status_code=404, detail="Employee not found")

@router.post("", status_code=201)
def create_employee(employee: Employee):
    new_employee = {
        "id": get_next_employee_id(),
        "name": employee.name,
    }

    data.employees.append(new_employee)

    return new_employee

@router.put("/{employee_id}")
def update_employee(employee_id: int, updated_employee: Employee):
    for employee in data.employees:
        if employee["id"] == employee_id:
            employee["name"] = updated_employee.name
            return employee

    raise HTTPException(status_code=404, detail="Employee not found")

@router.delete("/{employee_id}")
def delete_employee(employee_id: int):
    for employee in data.employees:
        if employee["id"] == employee_id:
            data.employees.remove(employee)
            return {"message": "Employee deleted successfully"}

    raise HTTPException(status_code=404, detail="Employee not found")
