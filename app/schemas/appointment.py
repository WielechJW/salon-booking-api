from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.schemas.price import Price
from app.services.booking_service import AppointmentStatus
from app.timezone import as_utc


class Appointment(BaseModel):
    employee_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    start_at: datetime
    client_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
    ]
    client_email: EmailStr = Field(max_length=254)
    client_phone: str = Field(pattern=r"^\+?[0-9]{7,15}$")

    @field_validator("client_phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().translate(str.maketrans("", "", " ()-"))

        return value

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must include a timezone offset")

        return as_utc(value)


class AppointmentResponse(BaseModel):
    id: int
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
