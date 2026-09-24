from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

AppointmentStatus = Literal[
    "pending",
    "confirmed",
    "cancelled",
    "completed",
]

class Appointment(BaseModel):
    employee_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    start_at: datetime
    client_name: str = Field(min_length=2, max_length=100)
    client_email: str = Field(min_length=5, max_length=254)
    client_phone: str = Field(min_length=7, max_length=20)

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus