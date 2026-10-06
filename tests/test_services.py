from decimal import Decimal

import pytest

from app.models.service import ServiceModel


def test_service_crud_uses_http_api(client):
    create_response = client.post(
        "/services",
        json={
            "name": "Modelowanie",
            "description": "Profesjonalne modelowanie włosów",
            "duration_minutes": 30,
            "price": 70,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    service_id = created["id"]
    assert created["name"] == "Modelowanie"

    get_response = client.get(f"/services/{service_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Modelowanie"

    list_response = client.get("/services")
    assert list_response.status_code == 200
    assert service_id in [
        service["id"] for service in list_response.json()
    ]

    update_response = client.put(
        f"/services/{service_id}",
        json={
            "name": "Modelowanie premium",
            "description": "Rozszerzone modelowanie włosów",
            "duration_minutes": 45,
            "price": 100,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Modelowanie premium"

    delete_response = client.delete(f"/services/{service_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Service deleted successfully"
    }

    missing_response = client.get(f"/services/{service_id}")
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Service not found"}


def test_invalid_service_payload_returns_422(client):
    response = client.post(
        "/services",
        json={
            "name": "M",
            "description": "Krótko",
            "duration_minutes": 0,
            "price": -1,
        },
    )

    assert response.status_code == 422
    error_fields = {
        error["loc"][-1] for error in response.json()["detail"]
    }
    assert error_fields == {"name", "duration_minutes", "price"}


@pytest.mark.parametrize("method", ["post", "put"])
@pytest.mark.parametrize(
    "price",
    [-0.01, 12.345, "0.001", "100000000", "Infinity", "-Infinity", "NaN"],
)
def test_invalid_price_returns_422_on_create_and_update(client, method, price):
    response = getattr(client, method)(
        "/services" if method == "post" else "/services/1",
        json={
            "name": "Modelowanie",
            "description": "Profesjonalne modelowanie włosów",
            "duration_minutes": 30,
            "price": price,
        },
    )

    assert response.status_code == 422
    assert {error["loc"][-1] for error in response.json()["detail"]} == {"price"}
    assert client.get("/services/1").json()["price"] == 80.0


@pytest.mark.parametrize("price", [0, "12.34", "12.3400", "99999999.99"])
def test_valid_price_is_persisted_without_rounding(client, database_session, price):
    response = client.post(
        "/services",
        json={
            "name": "Modelowanie",
            "description": "Profesjonalne modelowanie włosów",
            "duration_minutes": 30,
            "price": price,
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert isinstance(created["price"], (int, float))
    assert Decimal(str(created["price"])) == Decimal(str(price))
    stored = database_session.get(ServiceModel, created["id"])
    assert stored.price == Decimal(str(price))
