from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.appointments import router as appointments_router
from app.routers.auth import router as auth_router
from app.routers.availability import router as availability_router
from app.routers.employees import router as employees_router
from app.routers.schedules import router as schedules_router
from app.routers.services import router as services_router
from app.routers.time_off import router as time_off_router
from app.routers.users import router as users_router
from app.services.errors import (
    DomainConflictError,
    DomainNotFoundError,
    DomainValidationError,
)

app = FastAPI(
    title="Salon Booking API",
    description="API for managing salon services and bookings",
    version="1.0.0",
)


@app.exception_handler(DomainNotFoundError)
async def handle_domain_not_found(
    request: Request,
    error: DomainNotFoundError,
) -> JSONResponse:
    del request
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(DomainConflictError)
async def handle_domain_conflict(
    request: Request,
    error: DomainConflictError,
) -> JSONResponse:
    del request
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(DomainValidationError)
async def handle_domain_validation(
    request: Request,
    error: DomainValidationError,
) -> JSONResponse:
    del request
    return JSONResponse(status_code=422, content={"detail": str(error)})


app.include_router(services_router)
app.include_router(employees_router)
app.include_router(appointments_router)
app.include_router(schedules_router)
app.include_router(availability_router)
app.include_router(time_off_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "Salon Booking API"}
