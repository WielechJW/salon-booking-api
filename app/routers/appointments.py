from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.appointment import AppointmentModel
from app.models.user import UserModel
from app.schemas.appointment import (
    Appointment,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from app.schemas.appointment_list import PAGINATION_RESPONSES, AppointmentListParams
from app.services import booking_service
from app.services.appointment_list_service import list_appointments
from app.services.authorization import get_visible_appointment, scope_appointments
from app.timezone import utc_now

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get(
    "", response_model=list[AppointmentResponse], responses=PAGINATION_RESPONSES
)
def get_appointments(
    response: Response,
    params: Annotated[AppointmentListParams, Query()],
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    page = list_appointments(
        database_session=database_session,
        query=scope_appointments(select(AppointmentModel), user),
        **params.model_dump(),
    )
    response.headers["X-Total-Count"] = str(page.total)
    response.headers["X-Limit"] = str(page.limit)
    response.headers["X-Offset"] = str(page.offset)
    return page.items


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    return get_visible_appointment(
        database_session=database_session, appointment_id=appointment_id, user=user
    )


@router.post("", status_code=201, response_model=AppointmentResponse)
def create_appointment(
    appointment: Appointment,
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    payload = appointment.model_dump()
    client_id = payload.pop("client_id")
    if client_id is not None and client_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Cannot book for another user")
    return booking_service.create_appointment(
        database_session=database_session,
        client_id=client_id if client_id is not None else user.id,
        current_time=utc_now(),
        **payload,
    )


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    get_visible_appointment(
        database_session=database_session, appointment_id=appointment_id, user=user
    )
    if user.role == "CLIENT" and status_update.status != "cancelled":
        raise HTTPException(
            status_code=403, detail="Clients may only cancel appointments"
        )
    return booking_service.update_appointment_status(
        database_session=database_session,
        appointment_id=appointment_id,
        requested_status=status_update.status,
    )
