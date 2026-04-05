import json
from flask import Blueprint, jsonify, request
from app.models.event import Event
from app.models.url import URL
from app.models.user import User
from app.database import db

events_bp = Blueprint("events", __name__)


def get_next_event_id():
    last = Event.select().order_by(Event.id.desc()).first()
    return (last.id + 1) if last else 1


def format_details(details_field):
    if details_field is None:
        return None
    if isinstance(details_field, str):
        try:
            return json.loads(details_field)
        except (json.JSONDecodeError, TypeError):
            return details_field
    return details_field


@events_bp.route("/events", methods=["GET"])
def list_events():
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    event_type = request.args.get("event_type")
    user_id = request.args.get("user_id")
    url_id = request.args.get("url_id")

    # FIX FOR #2: Select all events (no JOIN/is_active filter)
    query = Event.select().order_by(Event.id)

    if event_type:
        query = query.where(Event.event_type == event_type)

    if user_id:
        # Error Code Fix: Return 404 if the filtered resource doesn't exist
        if not User.get_or_none(User.id == user_id):
            return jsonify({"error": "User not found"}), 404
        query = query.where(Event.user_id == int(user_id))

    if url_id:
        # Error Code Fix: Return 404 if the filtered resource doesn't exist
        if not URL.get_or_none(URL.id == url_id):
            return jsonify({"error": "URL not found"}), 404
        query = query.where(Event.url_id == int(url_id))

    total = query.count()
    p_int = int(page) if page else None
    pp_int = int(per_page) if per_page else None

    if p_int and pp_int:
        if p_int < 1 or pp_int < 1 or pp_int > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(p_int, pp_int)

    results = []
    for event in query:
        results.append({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": format_details(event.details)
        })

    return jsonify({
        "kind": "list",
        "sample": results,
        "metadata": {
            "total": total,
            "page": p_int,
            "per_page": pp_int
        }
    }), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    event_type = data.get("event_type")
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    details = data.get("details")

    if any(v is None for v in [event_type, url_id, user_id]):
        return jsonify({"error": "Missing required fields"}), 400

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    url = URL.get_or_none(URL.id == url_id)
    if not url:
        return jsonify({"error": "URL not found"}), 404

    # Challenge #2/4: POST requires active URL, return 404 for inactive ones
    if not url.is_active:
        return jsonify({"error": "URL is inactive"}), 404

    try:
        # Challenge #6: Use json.dumps to support non-dict types (strings/ints)
        db_details = json.dumps(details) if details is not None else None

        event = Event.create(
            id=get_next_event_id(),
            event_type=event_type,
            url=url,
            user=user,
            details=db_details
        )

        return jsonify({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": format_details(event.details)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500