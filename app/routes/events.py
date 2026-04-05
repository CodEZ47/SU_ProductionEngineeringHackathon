from flask import Blueprint, request, jsonify
from app.models.event import Event
from app.models.url import URL
from app.models.user import User

events_bp = Blueprint("events", __name__)


def serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url.id,
        "user_id": event.user.id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
        "details": event.details
    }


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    url_id = data.get("url_id")
    user_id = data.get("user_id")
    event_type = data.get("event_type")
    details = data.get("details", "")

    if url_id is None or user_id is None or event_type is None:
        return jsonify({"error": "Missing required fields"}), 400

    url = URL.get_or_none(URL.id == url_id)
    user = User.get_or_none(User.id == user_id)

    if url is None or user is None:
        return jsonify({"error": "Invalid url_id or user_id"}), 404

    event = Event.create(
        url=url,
        user=user,
        event_type=event_type,
        details=details
    )

    return jsonify(serialize_event(event)), 201


@events_bp.route("/events", methods=["GET"])
def get_events():
    url_id = request.args.get("url_id")
    user_id = request.args.get("user_id")

    query = Event.select()

    if url_id is not None:
        url = URL.get_or_none(URL.id == url_id)
        if url is None:
            return jsonify({"error": "URL not found"}), 404
        query = query.where(Event.url == url)

    if user_id is not None:
        user = User.get_or_none(User.id == user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 404
        query = query.where(Event.user == user)

    events = [serialize_event(e) for e in query]

    return jsonify(events), 200


@events_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(serialize_event(event)), 200


@events_bp.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    event_type = data.get("event_type")
    details = data.get("details")

    if event_type is not None:
        if not isinstance(event_type, str) or event_type.strip() == "":
            return jsonify({"error": "Invalid event_type"}), 400
        event.event_type = event_type

    if details is not None:
        event.details = details

    event.save()

    return jsonify(serialize_event(event)), 200


@events_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    event.delete_instance()

    return jsonify({"message": "Event deleted"}), 200