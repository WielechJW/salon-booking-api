from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.employee import EmployeeModel
from app.models.user import UserModel
from app.services.errors import DomainNotFoundError


def scope_appointments(query: Select, user: UserModel) -> Select:
    if user.role == "ADMIN":
        return query
    if user.role == "EMPLOYEE":
        return query.where(
            AppointmentModel.employee_id.in_(
                select(EmployeeModel.id).where(EmployeeModel.user_id == user.id)
            )
        )
    return query.where(AppointmentModel.client_id == user.id)


def get_visible_appointment(
    *, database_session: Session, appointment_id: int, user: UserModel
) -> AppointmentModel:
    appointment = database_session.scalar(
        scope_appointments(
            select(AppointmentModel).where(AppointmentModel.id == appointment_id), user
        )
    )
    if appointment is None:
        raise DomainNotFoundError("Appointment not found")
    return appointment
