from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import AppointmentModel
from app.models.service import ServiceModel
from app.schemas.service import Service, ServiceResponse


router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceResponse])
def get_services(database_session: Session = Depends(get_db)):
    query = select(ServiceModel).order_by(ServiceModel.id)
    return database_session.scalars(query).all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int,
    database_session: Session = Depends(get_db),
):
    service = database_session.get(ServiceModel, service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


@router.post("", status_code=201, response_model=ServiceResponse)
def create_service(
    service: Service,
    database_session: Session = Depends(get_db),
):
    new_service = ServiceModel(
        name=service.name,
        description=service.description,
        duration_minutes=service.duration_minutes,
        price=service.price,
    )

    database_session.add(new_service)
    database_session.commit()
    database_session.refresh(new_service)

    return new_service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    updated_service: Service,
    database_session: Session = Depends(get_db),
):
    service = database_session.get(ServiceModel, service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    service.name = updated_service.name
    service.description = updated_service.description
    service.duration_minutes = updated_service.duration_minutes
    service.price = updated_service.price

    database_session.commit()
    database_session.refresh(service)

    return service


@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    database_session: Session = Depends(get_db),
):
    service = database_session.get(ServiceModel, service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    appointment_id = database_session.scalar(
        select(AppointmentModel.id)
        .where(AppointmentModel.service_id == service_id)
        .limit(1)
    )

    if appointment_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Service has appointments and cannot be deleted",
        )

    database_session.delete(service)
    database_session.commit()

    return {"message": "Service deleted successfully"}
