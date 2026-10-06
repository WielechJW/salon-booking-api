from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Schedule(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @field_validator("start_time", "end_time")
    @classmethod
    def require_local_time(cls, value: time) -> time:
        if value.tzinfo is not None:
            raise ValueError("Schedule times must not include a timezone offset")

        return value

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")

        return self


class ScheduleResponse(Schedule):
    id: int
    employee_id: int

    model_config = ConfigDict(from_attributes=True)
