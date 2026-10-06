from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.schemas.contact import PersonName, PhoneNumber
from app.schemas.price import Price
from app.services.booking_service import AppointmentStatus
from app.timezone import as_utc


class Appointment(BaseModel):
    employee_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    start_at: datetime
    client_id: int | None = Field(default=None, gt=0)
    client_name: PersonName
    client_email: EmailStr = Field(max_length=254)
    client_phone: PhoneNumber

    model_config = ConfigDict(extra="forbid")

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must include a timezone offset")

        return as_utc(value)


class AppointmentResponse(BaseModel):
    id: int
    client_id: int | None
    employee_id: int
    service_id: int
    start_at: datetime
    client_name: str
    client_email: str
    client_phone: str
    duration_minutes: int
    price: Price
    end_at: datetime
    status: AppointmentStatus

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def serialize_database_datetime_as_utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    model_config = ConfigDict(from_attributes=True)


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
