from pydantic import BaseModel


class SalonInfo(BaseModel):
    timezone: str
