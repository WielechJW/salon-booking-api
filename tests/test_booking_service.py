from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models.schedule import ScheduleModel
from app.services import booking_service
from app.services.errors import DomainConflictError, DomainValidationError
from app.timezone import as_utc

WARSAW = ZoneInfo("Europe/Warsaw")
CURRENT_TIME = datetime(2026, 9, 24, 12, tzinfo=timezone.utc)


def add_friday_schedule(database_session) -> None:
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9),
            end_time=time(18),
        )
    )
    database_session.commit()


def create_booking(
    database_session,
    *,
    start_at: datetime,
    service_id: int = 1,
):
    return booking_service.create_appointment(
        database_session=database_session,
        employee_id=1,
        service_id=service_id,
        start_at=start_at,
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
        current_time=CURRENT_TIME,
    )


def test_booking_service_rejects_overlap_without_http_client(database_session):
    add_friday_schedule(database_session)
    created = create_booking(
        database_session,
        start_at=datetime(2026, 9, 25, 10, tzinfo=WARSAW),
    )

    assert as_utc(created.start_at) == datetime(
        2026,
        9,
        25,
        8,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        DomainConflictError,
        match="Employee already has an appointment at this time",
    ):
        create_booking(
            database_session,
            start_at=datetime(2026, 9, 25, 10, 30, tzinfo=WARSAW),
            service_id=2,
        )


def test_booking_service_requires_aware_datetime(database_session):
    add_friday_schedule(database_session)

    with pytest.raises(
        DomainValidationError,
        match="start_at must include a timezone offset",
    ):
        create_booking(
            database_session,
            start_at=datetime(2026, 9, 25, 10),
        )


def test_booking_service_enforces_status_transitions(database_session):
    add_friday_schedule(database_session)
    appointment = create_booking(
        database_session,
        start_at=datetime(2026, 9, 25, 10, tzinfo=WARSAW),
    )

    confirmed = booking_service.update_appointment_status(
        database_session=database_session,
        appointment_id=appointment.id,
        requested_status="confirmed",
    )
    assert confirmed.status == "confirmed"

    completed = booking_service.update_appointment_status(
        database_session=database_session,
        appointment_id=appointment.id,
        requested_status="completed",
    )
    assert completed.status == "completed"

    with pytest.raises(
        DomainConflictError,
        match="Cannot change appointment status from completed to pending",
    ):
        booking_service.update_appointment_status(
            database_session=database_session,
            appointment_id=appointment.id,
            requested_status="pending",
        )


def test_time_ranges_overlap_treats_adjacent_ranges_as_available():
    first_start = datetime(2026, 9, 25, 8, tzinfo=timezone.utc)
    first_end = datetime(2026, 9, 25, 8, 45, tzinfo=timezone.utc)

    assert booking_service.time_ranges_overlap(
        first_start,
        first_end,
        datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc),
        datetime(2026, 9, 25, 9, 30, tzinfo=timezone.utc),
    )
    assert not booking_service.time_ranges_overlap(
        first_start,
        first_end,
        datetime(2026, 9, 25, 8, 45, tzinfo=timezone.utc),
        datetime(2026, 9, 25, 9, 45, tzinfo=timezone.utc),
    )
