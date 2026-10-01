from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.timezone import as_utc


class EmployeeTimeOff(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: str = Field(min_length=2, max_length=500)

    @field_validator("start_at", "end_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("time off timestamps must include a timezone offset")

        return as_utc(value)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be before end_at")

        return self


class EmployeeTimeOffResponse(EmployeeTimeOff):
    id: int
    employee_id: int

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def serialize_database_datetime_as_utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    model_config = ConfigDict(from_attributes=True)
