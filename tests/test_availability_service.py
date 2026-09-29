from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from app.models.schedule import ScheduleModel
from app.services import availability_service, booking_service

WARSAW = ZoneInfo("Europe/Warsaw")


def test_availability_service_uses_shared_collision_rules(database_session):
    database_session.add(
        ScheduleModel(
            employee_id=1,
            day_of_week=4,
            start_time=time(9),
            end_time=time(12),
        )
    )
    database_session.commit()
    booking_service.create_appointment(
        database_session=database_session,
        employee_id=1,
        service_id=1,
        start_at=datetime(2026, 9, 25, 9, 45, tzinfo=WARSAW),
        client_name="Jan Kowalski",
        client_email="jan@example.com",
        client_phone="123456789",
        current_time=datetime(2026, 9, 24, 12, tzinfo=timezone.utc),
    )

    availability = availability_service.get_employee_availability(
        database_session=database_session,
        employee_id=1,
        service_id=1,
        target_date=date(2026, 9, 25),
    )

    assert availability.available_slots == (
        time(9),
        time(10, 30),
        time(11, 15),
    )
