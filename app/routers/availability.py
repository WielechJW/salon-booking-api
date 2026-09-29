from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.employee_service import EmployeeServiceModel
from app.models.schedule import ScheduleModel
from app.models.service import ServiceModel
from app.schemas.availability import AvailabilityResponse
from app.timezone import as_utc, get_salon_timezone

router = APIRouter(prefix="/employees", tags=["availability"])


@router.get(
    "/{employee_id}/availability",
    response_model=AvailabilityResponse,
)
def get_employee_availability(
    employee_id: int,
    target_date: date = Query(alias="date"),
    service_id: int = Query(gt=0),
    database_session: Session = Depends(get_db),
):
    employee = database_session.get(EmployeeModel, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    selected_service = database_session.get(ServiceModel, service_id)

    if selected_service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    assignment = database_session.get(
        EmployeeServiceModel,
        (employee_id, service_id),
    )

    if assignment is None:
        raise HTTPException(
            status_code=409,
            detail="Employee does not provide this service",
        )

    work_schedule = database_session.scalar(
        select(ScheduleModel).where(
            ScheduleModel.employee_id == employee_id,
            ScheduleModel.day_of_week == target_date.weekday(),
        )
    )

    if work_schedule is None:
        return AvailabilityResponse(
            employee_id=employee_id,
            service_id=service_id,
            date=target_date,
            available_slots=[],
        )

    salon_timezone = get_salon_timezone()
    local_work_start = datetime.combine(
        target_date,
        work_schedule.start_time,
        tzinfo=salon_timezone,
    )
    local_work_end = datetime.combine(
        target_date,
        work_schedule.end_time,
        tzinfo=salon_timezone,
    )
    work_start = as_utc(local_work_start)
    work_end = as_utc(local_work_end)
    appointments_query = select(AppointmentModel).where(
        AppointmentModel.employee_id == employee_id,
        AppointmentModel.start_at < work_end,
        AppointmentModel.end_at > work_start,
        AppointmentModel.status != "cancelled",
    )
    appointments = database_session.scalars(appointments_query).all()

    service_duration = timedelta(minutes=selected_service.duration_minutes)
    available_slots = []
    slot_start = work_start

    while slot_start + service_duration <= work_end:
        slot_end = slot_start + service_duration
        overlaps_appointment = False

        for existing_appointment in appointments:
            existing_start = as_utc(existing_appointment.start_at)
            existing_end = as_utc(existing_appointment.end_at)

            if slot_start < existing_end and slot_end > existing_start:
                overlaps_appointment = True
                break

        if not overlaps_appointment:
            available_slots.append(
                slot_start.astimezone(salon_timezone).time().replace(tzinfo=None)
            )

        slot_start += service_duration

    return AvailabilityResponse(
        employee_id=employee_id,
        service_id=service_id,
        date=target_date,
        available_slots=available_slots,
    )
