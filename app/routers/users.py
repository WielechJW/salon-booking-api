from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.user import UserModel
from app.schemas.appointment import AppointmentResponse
from app.schemas.appointment_list import PAGINATION_RESPONSES, AppointmentListParams
from app.schemas.user import UserResponse
from app.services.appointment_list_service import list_appointments

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    employee_id = database_session.scalar(
        select(EmployeeModel.id).where(EmployeeModel.user_id == user.id)
    )
    return UserResponse.model_validate(user).model_copy(
        update={"employee_id": employee_id}
    )


@router.get(
    "/me/appointments",
    response_model=list[AppointmentResponse],
    responses=PAGINATION_RESPONSES,
)
def get_my_appointments(
    response: Response,
    params: Annotated[AppointmentListParams, Query()],
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    page = list_appointments(
        database_session=database_session,
        query=select(AppointmentModel).where(AppointmentModel.client_id == user.id),
        **params.model_dump(),
    )
    response.headers["X-Total-Count"] = str(page.total)
    response.headers["X-Limit"] = str(page.limit)
    response.headers["X-Offset"] = str(page.offset)
    return page.items
