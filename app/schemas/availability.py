from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class AvailabilityResponse(BaseModel):
    employee_id: int
    service_id: int
    date: date
    available_slots: list[time]


class ServiceAvailabilitySlotResponse(BaseModel):
    employee_id: int
    employee_name: str
    start_at: datetime
    end_at: datetime

    model_config = ConfigDict(from_attributes=True)
