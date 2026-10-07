"""Disposable real FastAPI backend for browser tests; never uses the project's DB."""

import os
import secrets
import subprocess
import sys
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def serve(database_directory):
    os.environ["DATABASE_URL"] = f"sqlite:///{database_directory}/browser-test.db"
    os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)
    os.environ["SALON_TIMEZONE"] = "Europe/Warsaw"
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    import uvicorn

    from app.database import SessionLocal
    from app.models.employee import EmployeeModel
    from app.models.employee_service import EmployeeServiceModel
    from app.models.schedule import ScheduleModel
    from app.models.service import ServiceModel
    from app.models.user import UserModel
    from app.security import hash_password
    from app.services.booking_service import create_appointment

    with SessionLocal() as session:
        password_hash = hash_password("TestPassword123!")
        session.add_all(
            UserModel(
                email=email,
                password_hash=password_hash,
                first_name=first,
                last_name=last,
                phone="+48123456789",
                role=role,
                is_active=True,
            )
            for email, first, last, role in (
                ("admin@example.com", "Admin", "Salon", "ADMIN"),
                ("client@example.com", "Jan", "Kowalski", "CLIENT"),
                ("staff@example.com", "Anna", "Nowak", "EMPLOYEE"),
                ("other@example.com", "Inny", "Klient", "CLIENT"),
            )
        )
        session.flush()
        session.add_all(
            (
                EmployeeModel(name="Anna Nowak", user_id=3),
                EmployeeModel(name="Bartek Kowalski"),
                ServiceModel(
                    name="Strzyżenie",
                    description="Strzyżenie dopasowane do Ciebie i Twojego stylu.",
                    duration_minutes=45,
                    price=Decimal("90.00"),
                ),
                ServiceModel(
                    name="Modelowanie",
                    description="Lekkość, objętość i wykończenie na każdą okazję.",
                    duration_minutes=30,
                    price=Decimal("70.00"),
                ),
            )
        )
        session.flush()
        for employee_id in (1, 2):
            for service_id in (1, 2):
                session.add(
                    EmployeeServiceModel(employee_id=employee_id, service_id=service_id)
                )
            for day in range(7):
                session.add(
                    ScheduleModel(
                        employee_id=employee_id,
                        day_of_week=day,
                        start_time=time(9),
                        end_time=time(17),
                    )
                )
        session.commit()
        tomorrow = datetime.now(ZoneInfo("Europe/Warsaw")).date() + timedelta(days=1)
        for employee_id, hour in ((1, 11), (2, 12)):
            create_appointment(
                database_session=session,
                employee_id=employee_id,
                service_id=1,
                client_id=4,
                start_at=datetime.combine(
                    tomorrow, time(hour), tzinfo=ZoneInfo("Europe/Warsaw")
                ),
                client_name="Inny Klient",
                client_email="other@example.com",
                client_phone="+48987654321",
            )
    uvicorn.run("app.main:app", host="127.0.0.1", port=18100, log_level="warning")


if __name__ == "__main__":
    with TemporaryDirectory(prefix="salon-browser-test-") as directory:
        serve(directory)
