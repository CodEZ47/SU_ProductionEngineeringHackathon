def create_test_url(client):
    response = client.post("/urls", json={
        "user_id": 1,
        "original_url": "https://example.com/event-test",
        "title": "Event Test URL"
    })
    return response.get_json()["id"]


def test_create_event_missing_fields(client):
    response = client.post("/events", json={"event_type": "click"})
    assert response.status_code == 400


def test_create_event_invalid_user_id_type(client):
    response = client.post("/events", json={
        "event_type": "click",
        "url_id": 1,
        "user_id": "abc"
    })
    assert response.status_code == 400


def test_create_event_invalid_url_id_type(client):
    response = client.post("/events", json={
        "event_type": "click",
        "url_id": "abc",
        "user_id": 1
    })
    assert response.status_code == 400


def test_create_event_event_type_not_string(client):
    response = client.post("/events", json={
        "event_type": 123,
        "url_id": 1,
        "user_id": 1
    })
    assert response.status_code == 400


def test_create_event_invalid_details_type(client):
    response = client.post("/events", json={
        "event_type": "click",
        "url_id": 1,
        "user_id": 1,
        "details": "not-a-dict"
    })
    assert response.status_code == 400


def test_create_event_user_or_url_not_found(client):
    response = client.post("/events", json={
        "event_type": "click",
        "url_id": 999999,
        "user_id": 999999
    })
    assert response.status_code == 404


def test_create_event_success_with_details(client):
    url_id = create_test_url(client)

    response = client.post("/events", json={
        "event_type": "click",
        "url_id": url_id,
        "user_id": 1,
        "details": {"browser": "chrome"}
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["details"]["browser"] == "chrome"


def test_list_events_invalid_user_id_filter(client):
    response = client.get("/events?user_id=abc")
    assert response.status_code == 400


def test_list_events_invalid_url_id_filter(client):
    response = client.get("/events?url_id=abc")
    assert response.status_code == 400


def test_list_events_invalid_pagination_type(client):
    response = client.get("/events?page=abc&per_page=10")
    assert response.status_code == 400


def test_list_events_invalid_pagination_range(client):
    response = client.get("/events?page=0&per_page=101")
    assert response.status_code == 400


def test_list_events_filter_by_event_type(client):
    url_id = create_test_url(client)

    client.post("/events", json={
        "event_type": "click",
        "url_id": url_id,
        "user_id": 1
    })

    response = client.get("/events?event_type=click")
    assert response.status_code == 200
    data = response.get_json()
    assert "events" in data