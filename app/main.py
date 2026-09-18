from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Salon Booking API",
    description="API for managing salon services and bookings",
    version="1.0.0"
)

class Service(BaseModel):
    name: str
    duration_minutes: int
    price: float

services = [
    {
        "id": 1,
        "name": "Strzyżenie męskie",
        "duration_minutes": 45,
        "price": 80
    },
    {
        "id": 2,
        "name": "Strzyżenie damskie",
        "duration_minutes": 60,
        "price": 120
    }
]



@app.get("/")
def root():
    return {"message": "Salon Booking API"}

def get_next_service_id():
    if not services:
        return 1

    return max(service["id"] for service in services) + 1

@app.get("/services")
def get_services():
    return services

@app.get("/services/{service_id}")
def get_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            return service

    raise HTTPException(
        status_code=404,
        detail="Service not found"
    )

@app.post("/services")
def create_service(service: Service):
    new_service = {
        "id": get_next_service_id(),
        "name": service.name,
        "duration_minutes": service.duration_minutes,
        "price": service.price
    }

    services.append(new_service)

    return new_service

@app.delete("/services/{service_id}")
def delete_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            services.remove(service)

            return {
                "message": "Service deleted successfully"
            }

    raise HTTPException(
        status_code=404,
        detail="Service not found"
    )

@app.put("/services/{service_id}")
def update_service(service_id: int, updated_service: Service):
    for service in services:
        if service["id"] == service_id:
            service["name"] = updated_service.name
            service["duration_minutes"] = updated_service.duration_minutes
            service["price"] = updated_service.price

            return service

    raise HTTPException(
        status_code=404,
        detail="Service not found"
    )