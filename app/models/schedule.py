from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScheduleModel(Base):
    __tablename__ = "schedules"

    __table_args__ = (
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="ck_schedules_day_of_week",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="ck_schedules_start_before_end",
        ),
        UniqueConstraint(
            "employee_id",
            "day_of_week",
            name="uq_schedules_employee_day",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)