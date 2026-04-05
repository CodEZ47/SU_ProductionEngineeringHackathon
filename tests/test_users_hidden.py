def test_create_user_missing_body(client):
    response = client.post("/users")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid JSON"


def test_create_user_body_not_object(client):
    response = client.post("/users", json=["not", "an", "object"])
    assert response.status_code == 400


def test_create_user_missing_fields(client):
    response = client.post("/users", json={"username": "alice"})
    assert response.status_code == 400


def test_create_user_invalid_username(client):
    response = client.post("/users", json={
        "username": "a@",
        "email": "alice@test.com"
    })
    assert response.status_code == 422


def test_create_user_invalid_email(client):
    response = client.post("/users", json={
        "username": "alice123",
        "email": "not-an-email"
    })
    assert response.status_code == 422


def test_create_user_duplicate_email(client):
    client.post("/users", json={
        "username": "alice123",
        "email": "alice@test.com"
    })

    response = client.post("/users", json={
        "username": "alice456",
        "email": "alice@test.com"
    })

    assert response.status_code == 409


def test_list_users_invalid_pagination_type(client):
    response = client.get("/users?page=abc&per_page=10")
    assert response.status_code == 400


def test_list_users_invalid_pagination_range(client):
    response = client.get("/users?page=0&per_page=101")
    assert response.status_code == 400


def test_get_user_not_found(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_update_user_not_found(client):
    response = client.put("/users/999999", json={"username": "newname"})
    assert response.status_code == 404


def test_update_user_missing_username(client):
    response = client.put("/users/1", json={})
    assert response.status_code == 400


def test_update_user_invalid_username(client):
    response = client.put("/users/1", json={"username": "@bad"})
    assert response.status_code == 422


def test_delete_user_not_found(client):
    response = client.delete("/users/999999")
    assert response.status_code == 404