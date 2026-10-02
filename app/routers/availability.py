from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.availability import AvailabilityResponse
from app.services import availability_service
from app.timezone import utc_now

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
    availability = availability_service.get_employee_availability(
        database_session=database_session,
        employee_id=employee_id,
        service_id=service_id,
        target_date=target_date,
        current_time=utc_now(),
    )

    return AvailabilityResponse(
        employee_id=availability.employee_id,
        service_id=availability.service_id,
        date=availability.date,
        available_slots=list(availability.available_slots),
    )
