from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Schedule(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")

        return self


class ScheduleResponse(Schedule):
    id: int
    employee_id: int

    model_config = ConfigDict(from_attributes=True)