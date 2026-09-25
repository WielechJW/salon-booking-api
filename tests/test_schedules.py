from datetime import time

import pytest
from fastapi import HTTPException

from app.routers.schedules import (
    create_schedule,
    get_employee_schedule,
    update_schedule,
)
from app.schemas.schedule import Schedule


def make_schedule(
    day_of_week: int,
    start_time: time = time(9, 0),
    end_time: time = time(17, 0),
) -> Schedule:
    return Schedule(
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
    )


def test_schedule_can_be_created(database_session):
    created = create_schedule(
        1,
        make_schedule(day_of_week=0),
        database_session,
    )

    assert created.id is not None
    assert created.employee_id == 1
    assert created.day_of_week == 0
    assert created.start_time == time(9, 0)
    assert created.end_time == time(17, 0)


def test_employee_schedule_is_sorted_by_day(database_session):
    create_schedule(1, make_schedule(day_of_week=2), database_session)
    create_schedule(1, make_schedule(day_of_week=0), database_session)

    schedules = get_employee_schedule(1, database_session)

    assert [schedule.day_of_week for schedule in schedules] == [0, 2]


def test_schedule_can_be_updated(database_session):
    create_schedule(1, make_schedule(day_of_week=0), database_session)

    updated = update_schedule(
        1,
        make_schedule(
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(16, 0),
        ),
        database_session,
    )

    assert updated.start_time == time(8, 0)
    assert updated.end_time == time(16, 0)


def test_duplicate_schedule_is_rejected(database_session):
    create_schedule(1, make_schedule(day_of_week=0), database_session)

    with pytest.raises(HTTPException) as error:
        create_schedule(
            1,
            make_schedule(day_of_week=0),
            database_session,
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Schedule for this day already exists"