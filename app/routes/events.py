import json
from flask import Blueprint, jsonify, request
from app.models.event import Event
from app.models.url import URL
from app.models.user import User
from app.database import db

events_bp = Blueprint("events", __name__)


def sync_event_id_sequence():
    db.execute_sql("""
        SELECT setval(
            pg_get_serial_sequence('"event"', 'id'),
            COALESCE((SELECT MAX(id) FROM "event"), 1),
            true
        );
    """)


@events_bp.route("/events", methods=["GET"])
def list_events():
    event_type = request.args.get("event_type")
    user_id = request.args.get("user_id")
    url_id = request.args.get("url_id")
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    query = Event.select()
    if event_type:
        query = query.where(Event.event_type == event_type)
    if user_id is not None:
        try:
            user_id = int(user_id)
            query = query.where(Event.user_id == user_id)
        except ValueError:
            return jsonify({"error": "user_id must be an integer"}), 400
    if url_id is not None:
        try:
            url_id = int(url_id)
            query = query.where(Event.url_id == url_id)
        except ValueError:
            return jsonify({"error": "url_id must be an integer"}), 400

    query = query.order_by(Event.timestamp.desc())
    total = query.count()

    if page is not None and per_page is not None:
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError:
            return jsonify({"error": "page and per_page must be integers"}), 400
        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(page, per_page)

    result = []
    for event in query:
        details = None
        if event.details:
            try:
                details = json.loads(event.details) if isinstance(event.details, str) else event.details
            except (json.JSONDecodeError, TypeError):
                details = event.details

        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else event.timestamp,
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": details
        })

    return jsonify({
        "kind": "list",
        "sample": result,
        "metadata": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    event_type = data.get("event_type")
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    details = data.get("details")

    ALLOWED_TYPES = {"created", "clicked", "deleted", "updated"}
    if event_type not in ALLOWED_TYPES:
        return jsonify({"error": "Invalid event type"}), 422

    if url_id is None or user_id is None:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.get_or_none(User.id == user_id)
    url = URL.get_or_none(URL.id == url_id)
    if not user or not url:
        return jsonify({"error": "User or URL not found"}), 404

    try:
        sync_event_id_sequence()
        event = Event.create(
            event_type=event_type,
            url=url,
            user=user,
            details=json.dumps(details) if details else None
        )
        return jsonify({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": details
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500