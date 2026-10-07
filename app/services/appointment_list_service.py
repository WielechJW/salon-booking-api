from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.services.booking_service import AppointmentStatus
from app.services.errors import DomainValidationError
from app.timezone import as_utc, get_salon_timezone


@dataclass(frozen=True)
class AppointmentPage:
    items: Sequence[AppointmentModel]
    total: int
    limit: int
    offset: int


def list_appointments(
    *,
    database_session: Session,
    query: Select,
    employee_id: int | None = None,
    status: AppointmentStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> AppointmentPage:
    if employee_id is not None:
        query = query.where(AppointmentModel.employee_id == employee_id)
    if status is not None:
        query = query.where(AppointmentModel.status == status)
    salon_timezone = get_salon_timezone()
    try:
        if date_from is not None:
            start = as_utc(datetime.combine(date_from, time.min, tzinfo=salon_timezone))
            query = query.where(AppointmentModel.start_at >= start)
        if date_to is not None:
            end = as_utc(
                datetime.combine(
                    date_to + timedelta(days=1), time.min, tzinfo=salon_timezone
                )
            )
            query = query.where(AppointmentModel.start_at < end)
    except OverflowError as error:
        raise DomainValidationError(
            "Date range cannot be represented in UTC"
        ) from error

    total = database_session.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    )
    items = database_session.scalars(
        query.order_by(AppointmentModel.start_at, AppointmentModel.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return AppointmentPage(items=items, total=total or 0, limit=limit, offset=offset)
