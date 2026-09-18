from fastapi import FastAPI

app = FastAPI(
    title="Salon Booking API",
    description="API for managing salon services and bookings",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Salon Booking API"}

@app.get("/services")
def get_services():
    return [
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