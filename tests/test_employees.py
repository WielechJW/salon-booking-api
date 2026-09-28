def test_employee_crud_uses_http_api(client):
    create_response = client.post(
        "/employees",
        json={"name": "Kamil Wiśniewski"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    employee_id = created["id"]
    assert created["name"] == "Kamil Wiśniewski"

    get_response = client.get(f"/employees/{employee_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Kamil Wiśniewski"

    list_response = client.get("/employees")
    assert list_response.status_code == 200
    assert employee_id in [
        employee["id"] for employee in list_response.json()
    ]

    update_response = client.put(
        f"/employees/{employee_id}",
        json={"name": "Kamil Nowak"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Kamil Nowak"

    delete_response = client.delete(f"/employees/{employee_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Employee deleted successfully"
    }

    missing_response = client.get(f"/employees/{employee_id}")
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Employee not found"}


def test_service_can_be_assigned_to_employee(client):
    response = client.post("/employees/2/services/1")

    assert response.status_code == 201
    assert response.json() == {
        "message": "Service assigned to employee"
    }

    services_response = client.get("/employees/2/services")
    assert services_response.status_code == 200
    assert [
        service["id"] for service in services_response.json()
    ] == [1]


def test_employee_services_are_returned(client):
    response = client.get("/employees/1/services")

    assert response.status_code == 200
    assert [service["id"] for service in response.json()] == [1, 2]


def test_service_can_be_removed_from_employee(client):
    response = client.delete("/employees/1/services/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Service removed from employee"
    }

    services_response = client.get("/employees/1/services")
    assert services_response.status_code == 200
    assert [
        service["id"] for service in services_response.json()
    ] == [2]
