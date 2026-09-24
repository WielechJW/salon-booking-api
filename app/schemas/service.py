from pydantic import BaseModel, ConfigDict, Field


class Service(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    duration_minutes: int = Field(gt=0)
    price: float = Field(ge=0)


class ServiceResponse(Service):
    id: int

    model_config = ConfigDict(from_attributes=True)
