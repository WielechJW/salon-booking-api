from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmployeeServiceModel(Base):
    __tablename__ = "employee_services"

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    )
