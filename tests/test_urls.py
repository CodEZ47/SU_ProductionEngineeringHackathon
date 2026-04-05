import pytest
from peewee import DataError


def test_create_url_success(client):
    response = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com/test",
        "title": "Test URL"
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["original_url"] == "https://example.com/test"


def test_create_url_invalid_url(client):
    response = client.post("/urls", json={
        "user_id": 1,
        "original_url": "not-a-url"
    })

    assert response.status_code == 400


def test_create_url_missing_fields(client):
    response = client.post("/urls", json={})
    assert response.status_code == 400


def test_create_url_invalid_user_id_type(client):
    response = client.post("/urls", json={
        "user_id": "abc",
        "original_url": "https://example.com"
    })
    assert response.status_code == 400


def test_create_url_user_not_found(client):
    response = client.post("/urls", json={
        "user_id": 99999,
        "original_url": "https://example.com"
    })
    assert response.status_code in (400, 404)


def test_create_url_empty_url(client):
    response = client.post("/urls", json={
        "user_id": 1,
        "original_url": ""
    })
    assert response.status_code == 400


def test_create_url_title_too_long(client):
    with pytest.raises(DataError):
        client.post("/urls", json={
            "user_id": 1,
            "original_url": "https://example.com",
            "title": "x" * 300
        })


def test_get_urls(client):
    response = client.get("/urls")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_url_by_id(client):
    res = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com/a"
    })
    url_id = res.get_json()["id"]

    response = client.get(f"/urls/{url_id}")
    assert response.status_code == 200


def test_get_url_not_found(client):
    response = client.get("/urls/99999")
    assert response.status_code == 404


def test_update_url(client):
    res = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com/update"
    })
    url_id = res.get_json()["id"]

    response = client.put(f"/urls/{url_id}", json={
        "title": "Updated Title"
    })

    assert response.status_code == 200
    assert response.get_json()["title"] == "Updated Title"


def test_update_url_not_found(client):
    response = client.put("/urls/9999", json={
        "title": "Doesn't exist"
    })
    assert response.status_code == 404


def test_update_url_invalid_is_active(client):
    res = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com"
    })
    url_id = res.get_json()["id"]

    response = client.put(f"/urls/{url_id}", json={
        "is_active": "not-a-bool"
    })
    assert response.status_code == 400


def test_delete_url(client):
    res = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com/delete"
    })
    url_id = res.get_json()["id"]

    response = client.delete(f"/urls/{url_id}")
    assert response.status_code == 204


def test_delete_url_not_found(client):
    response = client.delete("/urls/9999")
    assert response.status_code == 404


def test_filter_urls_by_user(client):
    response = client.get("/urls?user_id=1")
    assert response.status_code == 200


def test_filter_urls_by_active(client):
    response = client.get("/urls?is_active=true")
    assert response.status_code == 200


def test_filter_urls_invalid_is_active(client):
    response = client.get("/urls?is_active=notabool")
    assert response.status_code in (200, 400)