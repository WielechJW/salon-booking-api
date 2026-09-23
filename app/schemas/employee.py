from pydantic import BaseModel, Field

class Employee(BaseModel):
    name: str = Field(min_length=2, max_length=100)