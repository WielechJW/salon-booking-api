import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timezone
from threading import Event
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import AppointmentModel
from app.models.schedule import ScheduleModel
from app.services import booking_service, schedule_service
from app.services.calendar_service import lock_employee_calendar
from app.services.errors import DomainConflictError

POSTGRES_TESTS_ENABLED = os.getenv("TEST_DATABASE_URL", "").startswith("postgresql")
CURRENT_TIME = datetime(2026, 9, 24, 12, tzinfo=timezone.utc)


@pytest.mark.skipif(
    not POSTGRES_TESTS_ENABLED,
    reason="Row-level locking requires PostgreSQL",
)
@pytest.mark.postgres
@pytest.mark.parametrize("first_operation", ["booking", "schedule"])
def test_booking_and_schedule_change_are_serialized(
    database_session, monkeypatch, first_operation
):
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9),
            end_time=time(17),
        )
    )
    database_session.commit()
    first_locked = Event()
    second_attempted_lock = Event()

    def first_lock(**kwargs):
        lock_employee_calendar(**kwargs)
        first_locked.set()
        assert second_attempted_lock.wait(timeout=5)

    def second_lock(**kwargs):
        assert first_locked.wait(timeout=5)
        second_attempted_lock.set()
        lock_employee_calendar(**kwargs)

    for operation, module in (
        ("booking", booking_service),
        ("schedule", schedule_service),
    ):
        monkeypatch.setattr(
            module,
            "lock_employee_calendar",
            first_lock if operation == first_operation else second_lock,
        )

    test_engine = database_session.get_bind()

    def run_operation(operation):
        with Session(test_engine) as session:
            try:
                if operation == "booking":
                    booking_service.create_appointment(
                        database_session=session,
                        employee_id=1,
                        service_id=1,
                        start_at=datetime(
                            2026, 9, 25, 10, tzinfo=ZoneInfo("Europe/Warsaw")
                        ),
                        client_name="Jan Kowalski",
                        client_email="jan@example.com",
                        client_phone="123456789",
                        current_time=CURRENT_TIME,
                    )
                    return 201

                schedule_service.update_employee_schedule(
                    database_session=session,
                    employee_id=1,
                    day_of_week=4,
                    start_time=time(9),
                    end_time=time(10),
                    current_time=CURRENT_TIME,
                )
                return 200
            except DomainConflictError:
                return 409

    second_operation = "schedule" if first_operation == "booking" else "booking"
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(run_operation, first_operation)
        second = executor.submit(run_operation, second_operation)
        assert first.result(timeout=10) == (
            201 if first_operation == "booking" else 200
        )
        assert second.result(timeout=10) == 409

    database_session.expire_all()
    schedule = database_session.scalar(select(ScheduleModel))
    appointments = database_session.scalars(select(AppointmentModel)).all()
    assert schedule.end_time == (time(17) if first_operation == "booking" else time(10))
    assert len(appointments) == (1 if first_operation == "booking" else 0)
