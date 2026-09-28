def make_schedule(
    day_of_week: int,
    start_time: str = "09:00:00",
    end_time: str = "17:00:00",
) -> dict:
    return {
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
    }


def test_schedule_can_be_created(client):
    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["id"] is not None
    assert created["employee_id"] == 1
    assert created["day_of_week"] == 0
    assert created["start_time"] == "09:00:00"
    assert created["end_time"] == "17:00:00"


def test_employee_schedule_is_sorted_by_day(client):
    assert client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=2),
    ).status_code == 201
    assert client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    ).status_code == 201

    response = client.get("/employees/1/schedule")

    assert response.status_code == 200
    assert [
        schedule["day_of_week"] for schedule in response.json()
    ] == [0, 2]


def test_schedule_can_be_updated(client):
    assert client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    ).status_code == 201

    response = client.put(
        "/employees/1/schedule",
        json=make_schedule(
            day_of_week=0,
            start_time="08:00:00",
            end_time="16:00:00",
        ),
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "08:00:00"
    assert response.json()["end_time"] == "16:00:00"


def test_duplicate_schedule_is_rejected(client):
    assert client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    ).status_code == 201

    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(day_of_week=0),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Schedule for this day already exists"
    }


def test_invalid_schedule_time_range_returns_422(client):
    response = client.post(
        "/employees/1/schedule",
        json=make_schedule(
            day_of_week=0,
            start_time="17:00:00",
            end_time="09:00:00",
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]
