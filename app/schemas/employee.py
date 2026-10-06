from pydantic import BaseModel, ConfigDict, Field


class Employee(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class EmployeeResponse(Employee):
    id: int

    model_config = ConfigDict(from_attributes=True)


class EmployeeAccountAssignment(BaseModel):
    user_id: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")
