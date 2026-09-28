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
