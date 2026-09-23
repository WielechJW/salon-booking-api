from fastapi import FastAPI

from app.routers.services import router as services_router
from app.routers.employees import router as employees_router

app = FastAPI(
    title="Salon Booking API",
    description="API for managing salon services and bookings",
    version="1.0.0",
)

app.include_router(services_router)
app.include_router(employees_router)

@app.get("/")
def root():
    return {"message": "Salon Booking API"}
