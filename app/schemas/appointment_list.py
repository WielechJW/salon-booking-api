from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.booking_service import AppointmentStatus


class AppointmentListParams(BaseModel):
    employee_id: int | None = Field(default=None, gt=0, le=2147483647)
    status: AppointmentStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=9223372036854775807)

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must not be after date_to")
        return self

    model_config = ConfigDict(extra="forbid")


PAGINATION_RESPONSES = {
    200: {
        "headers": {
            "X-Total-Count": {
                "description": "Number of matching appointments visible to the user",
                "schema": {"type": "integer"},
            },
            "X-Limit": {"schema": {"type": "integer"}},
            "X-Offset": {"schema": {"type": "integer"}},
        }
    }
}
