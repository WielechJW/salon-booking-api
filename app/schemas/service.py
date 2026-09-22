from pydantic import BaseModel

class Service(BaseModel):
    name: str
    description: str
    duration_minutes: int
    price: float