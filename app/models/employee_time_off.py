from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmployeeTimeOffModel(Base):
    __tablename__ = "employee_time_offs"
    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="ck_employee_time_offs_end_after_start",
        ),
        Index(
            "ix_employee_time_offs_employee_time_range",
            "employee_id",
            "start_at",
            "end_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
