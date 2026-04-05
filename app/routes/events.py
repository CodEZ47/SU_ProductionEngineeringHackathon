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

    query = Event.select().order_by(Event.id)

    if event_type:
        query = query.where(Event.event_type == event_type)

    if user_id:
        try:
            query = query.where(Event.user_id == int(user_id))
        except ValueError:
            return jsonify({"error": "Invalid user_id"}), 400

    if url_id:
        try:
            query = query.where(Event.url_id == int(url_id))
        except ValueError:
            return jsonify({"error": "Invalid url_id"}), 400

    total = query.count()

    if page is not None and per_page is not None:
        try:
            page_int = int(page)
            per_page_int = int(per_page)
        except ValueError:
            return jsonify({"error": "page and per_page must be integers"}), 400

        if page_int < 1 or per_page_int < 1 or per_page_int > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(page_int, per_page_int)

    results = []
    for event in query:
        results.append({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else event.timestamp,
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": format_details(event.details)
        })

    return jsonify({
        "kind": "list",
        "sample": results,
        "metadata": {
            "total": total,
            "page": int(page) if page else None,
            "per_page": int(per_page) if per_page else None
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

    url = URL.get_or_none((URL.id == url_id) & (URL.is_active == True))
    if not url:
        return jsonify({"error": "URL not found or inactive"}), 404

    try:
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
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else event.timestamp,
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": format_details(event.details)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500