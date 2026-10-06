from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.appointment import AppointmentModel
from app.models.user import UserModel
from app.schemas.appointment import AppointmentResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(user: UserModel = Depends(get_current_user)):
    return user


@router.get("/me/appointments", response_model=list[AppointmentResponse])
def get_my_appointments(
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
):
    return database_session.scalars(
        select(AppointmentModel)
        .where(AppointmentModel.client_id == user.id)
        .order_by(AppointmentModel.start_at, AppointmentModel.id)
    ).all()
