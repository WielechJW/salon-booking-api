from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import EmployeeModel
from app.models.schedule import ScheduleModel
from app.schemas.schedule import Schedule, ScheduleResponse


router = APIRouter(prefix="/employees", tags=["schedules"])


@router.post(
    "/{employee_id}/schedule",
    status_code=201,
    response_model=ScheduleResponse,
)
def create_schedule(
    employee_id: int,
    schedule: Schedule,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing_schedule = database_session.scalar(
        select(ScheduleModel).where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == schedule.day_of_week,
        )
    )

    if existing_schedule is not None:
        raise HTTPException(
            status_code=409,
            detail="Schedule for this day already exists",
        )

    new_schedule = ScheduleModel(
        employee_id=employee_id,
        **schedule.model_dump(),
    )

    database_session.add(new_schedule)
    database_session.commit()
    database_session.refresh(new_schedule)

    return new_schedule

@router.get(
    "/{employee_id}/schedule",
    response_model=list[ScheduleResponse],
)
def get_employee_schedule(
    employee_id: int,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    query = (
        select(ScheduleModel)
        .where(ScheduleModel.employee_id == employee_id)
        .order_by(ScheduleModel.day_of_week)
    )

    return database_session.scalars(query).all()

@router.put(
    "/{employee_id}/schedule",
    response_model=ScheduleResponse,
)
def update_schedule(
    employee_id: int,
    schedule: Schedule,
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing_schedule = database_session.scalar(
        select(ScheduleModel).where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == schedule.day_of_week,
        )
    )

    if existing_schedule is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule for this day not found",
        )

    existing_schedule.start_time = schedule.start_time
    existing_schedule.end_time = schedule.end_time

    database_session.commit()
    database_session.refresh(existing_schedule)

    return existing_schedule