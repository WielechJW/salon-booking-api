from datetime import date, time

from pydantic import BaseModel


class AvailabilityResponse(BaseModel):
    employee_id: int
    service_id: int
    date: date
    available_slots: list[time]
