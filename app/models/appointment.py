from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppointmentModel(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0",
            name="ck_appointments_duration_positive",
        ),
        CheckConstraint(
            "price >= 0",
            name="ck_appointments_price_nonnegative",
        ),
        CheckConstraint(
            "end_at > start_at",
            name="ck_appointments_end_after_start",
        ),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled', 'completed')",
            name="ck_appointments_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_email: Mapped[str] = mapped_column(String(254), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
