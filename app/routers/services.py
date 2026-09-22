from fastapi import APIRouter, HTTPException

from app.data import services
from app.schemas.service import Service


router = APIRouter(prefix="/services", tags=["services"])


def get_next_service_id():
    if not services:
        return 1

    return max(service["id"] for service in services) + 1


@router.get("")
def get_services():
    return services


@router.get("/{service_id}")
def get_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            return service

    raise HTTPException(status_code=404, detail="Service not found")


@router.post("")
def create_service(service: Service):
    if service.duration_minutes <= 0:
        raise HTTPException(
            status_code=400, detail="Duration must be a positive integer"
        )
    if service.price < 0:
        raise HTTPException(
            status_code=400, detail="Price must be a non-negative number"
        )

    new_service = {
        "id": get_next_service_id(),
        "name": service.name,
        "description": service.description,
        "duration_minutes": service.duration_minutes,
        "price": service.price,
    }

    services.append(new_service)

    return new_service


@router.delete("/{service_id}")
def delete_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            services.remove(service)

            return {"message": "Service deleted successfully"}

    raise HTTPException(status_code=404, detail="Service not found")


@router.put("/{service_id}")
def update_service(service_id: int, updated_service: Service):
    if updated_service.duration_minutes <= 0:
        raise HTTPException(
            status_code=400, detail="Duration must be a positive integer"
        )
    if updated_service.price < 0:
        raise HTTPException(
            status_code=400, detail="Price must be a non-negative number"
        )

    for service in services:
        if service["id"] == service_id:
            service["name"] = updated_service.name
            service["description"] = updated_service.description
            service["duration_minutes"] = updated_service.duration_minutes
            service["price"] = updated_service.price

            return service

    raise HTTPException(status_code=404, detail="Service not found")
