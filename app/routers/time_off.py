from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.employee_time_off import EmployeeTimeOff, EmployeeTimeOffResponse
from app.services import time_off_service

router = APIRouter(prefix="/employees", tags=["time off"])


@router.post(
    "/{employee_id}/time-off",
    status_code=201,
    response_model=EmployeeTimeOffResponse,
)
def create_time_off(
    employee_id: int,
    time_off: EmployeeTimeOff,
    database_session: Session = Depends(get_db),
):
    return time_off_service.create_time_off(
        database_session=database_session,
        employee_id=employee_id,
        **time_off.model_dump(),
    )


@router.get(
    "/{employee_id}/time-off",
    response_model=list[EmployeeTimeOffResponse],
)
def get_employee_time_offs(
    employee_id: int,
    database_session: Session = Depends(get_db),
):
    return time_off_service.list_employee_time_offs(
        database_session=database_session,
        employee_id=employee_id,
    )


@router.put(
    "/{employee_id}/time-off/{time_off_id}",
    response_model=EmployeeTimeOffResponse,
)
def update_time_off(
    employee_id: int,
    time_off_id: int,
    time_off: EmployeeTimeOff,
    database_session: Session = Depends(get_db),
):
    return time_off_service.update_time_off(
        database_session=database_session,
        employee_id=employee_id,
        time_off_id=time_off_id,
        **time_off.model_dump(),
    )


@router.delete("/{employee_id}/time-off/{time_off_id}")
def delete_time_off(
    employee_id: int,
    time_off_id: int,
    database_session: Session = Depends(get_db),
):
    time_off_service.delete_time_off(
        database_session=database_session,
        employee_id=employee_id,
        time_off_id=time_off_id,
    )
    return {"message": "Time off deleted successfully"}
