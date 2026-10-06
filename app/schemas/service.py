from pydantic import BaseModel, ConfigDict, Field

from app.schemas.price import Price


class Service(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    duration_minutes: int = Field(gt=0)
    price: Price


class ServiceResponse(Service):
    id: int

    model_config = ConfigDict(from_attributes=True)
