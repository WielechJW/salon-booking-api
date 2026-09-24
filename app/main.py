from fastapi import FastAPI

import app.models  # Registers all SQLAlchemy models.
from app.database import Base, engine
from app.routers.appointments import router as appointments_router
from app.routers.employees import router as employees_router
from app.routers.services import router as services_router


# Temporary during development. Alembic will manage tables later.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Salon Booking API",
    description="API for managing salon services and bookings",
    version="1.0.0",
)

app.include_router(services_router)
app.include_router(employees_router)
app.include_router(appointments_router)


@app.get("/")
def root():
    return {"message": "Salon Booking API"}
