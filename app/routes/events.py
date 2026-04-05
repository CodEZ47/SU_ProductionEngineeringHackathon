import json
from flask import Blueprint, jsonify, request
from app.models.event import Event
from app.models.url import URL
from app.models.user import User
from app.database import db
from datetime import datetime

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
    user_id_arg = request.args.get("user_id")
    url_id_arg = request.args.get("url_id")
    page_arg = request.args.get("page")
    per_page_arg = request.args.get("per_page")

    query = Event.select()

    if event_type:
        query = query.where(Event.event_type == event_type)

    if user_id_arg is not None:
        try:
            query = query.where(Event.user_id == int(user_id_arg))
        except (ValueError, TypeError):
            return jsonify({"error": "user_id must be an integer"}), 400

    if url_id_arg is not None:
        try:
            query = query.where(Event.url_id == int(url_id_arg))
        except (ValueError, TypeError):
            return jsonify({"error": "url_id must be an integer"}), 400

    total = query.count()
    query = query.order_by(Event.timestamp.desc(), Event.id.desc())

    page = None
    per_page = None

    if page_arg is not None or per_page_arg is not None:
        try:
            page = int(page_arg) if page_arg else 1
            per_page = int(per_page_arg) if per_page_arg else 10
        except ValueError:
            return jsonify({"error": "page and per_page must be integers"}), 400

        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(page, per_page)

    result = []
    for event in query:
        details = {}
        if event.details:
            try:
                details = json.loads(event.details) if isinstance(event.details, str) else event.details
            except:
                details = {}

        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": details if isinstance(details, dict) else {}
        })

    return jsonify({
        "events": result,
        "total": total,
        "page": page,
        "per_page": per_page
    }), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    if not all(k in data for k in ["event_type", "url_id", "user_id"]):
        return jsonify({"error": "Missing required fields"}), 400

    event_type = data.get("event_type")
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    details = data.get("details")

    if not isinstance(user_id, int) or not isinstance(url_id, int):
        return jsonify({"error": "user_id and url_id must be integers"}), 400

    if not isinstance(event_type, str) or not event_type.strip():
        return jsonify({"error": "event_type must be a string"}), 400

    if details is not None and not isinstance(details, dict):
        return jsonify({"error": "Details must be a JSON object"}), 400

    user = User.get_or_none(User.id == user_id)
    url = URL.get_or_none(URL.id == url_id)

    if not user or not url:
        return jsonify({"error": "User or URL not found"}), 404

    try:
        sync_event_id_sequence()

        now = datetime.now()

        event = Event.create(
            event_type=event_type,
            url=url,
            user=user,
            timestamp=now,
            details=json.dumps(details if details is not None else {})
        )

        return jsonify({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": details if details is not None else {}
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500