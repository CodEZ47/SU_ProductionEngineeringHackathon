
def test_create_url_creates_created_event(client):
    create_response = client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/integration-created",
            "title": "Integration Created"
        }
    )

    assert create_response.status_code == 201
    created_url = create_response.get_json()
    url_id = created_url["id"]

    events_response = client.get(f"/events?url_id={url_id}")
    assert events_response.status_code == 200

    data = events_response.get_json()
    assert "events" in data
    assert "total" in data
    assert data["total"] >= 1

    event_types = [event["event_type"] for event in data["events"]]
    assert "created" in event_types

    created_events = [event for event in data["events"] if event["event_type"] == "created"]
    assert len(created_events) >= 1

    event = created_events[0]
    assert event["url_id"] == url_id
    assert event["user_id"] == 1
    assert isinstance(event["details"], dict)


def test_events_endpoint_returns_expected_shape(client):
    response = client.get("/events")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, dict)
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)
    assert isinstance(data["total"], int)


def test_filter_events_by_url_id(client):
    first = client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/filter-one",
            "title": "Filter One"
        }
    )
    second = client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/filter-two",
            "title": "Filter Two"
        }
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_url_id = first.get_json()["id"]

    response = client.get(f"/events?url_id={first_url_id}")
    assert response.status_code == 200

    data = response.get_json()
    assert "events" in data

    for event in data["events"]:
        assert event["url_id"] == first_url_id


def test_filter_events_by_event_type_created(client):
    client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/created-only",
            "title": "Created Only"
        }
    )

    response = client.get("/events?event_type=created")
    assert response.status_code == 200

    data = response.get_json()
    assert "events" in data

    for event in data["events"]:
        assert event["event_type"] == "created"


def test_filter_events_by_user_id(client):
    client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/user-filter",
            "title": "User Filter"
        }
    )

    response = client.get("/events?user_id=1")
    assert response.status_code == 200

    data = response.get_json()
    assert "events" in data

    for event in data["events"]:
        assert event["user_id"] == 1
def test_full_user_flow_events(client):
    create_response = client.post(
        "/urls",
        json={
            "user_id": 1,
            "original_url": "https://example.com/full-flow",
            "title": "Full Flow"
        }
    )
    assert create_response.status_code == 201

    url_data = create_response.get_json()
    url_id = url_data["id"]
    short_code = url_data["short_code"]

    visit_response = client.get(f"/{short_code}")
    assert visit_response.status_code in (301, 302)

    events_response = client.get(f"/events?url_id={url_id}")
    assert events_response.status_code == 200

    data = events_response.get_json()
    event_types = [e["event_type"] for e in data["events"]]

    assert "created" in event_types
    assert "visited" in event_types or "click" in event_types