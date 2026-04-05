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
            pg_get_serial_sequence('event', 'id'),
            COALESCE((SELECT MAX(id) FROM event), 0) + 1,
            false
        );
    """)


def create_event_record(event_type, url, user, details=None):
    sync_event_id_sequence()
    event = Event.create(
        event_type=event_type,
        url=url,
        user=user,
        details=json.dumps(details) if details is not None else None
    )
    return event


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
            u_id = int(user_id)
            if not User.get_or_none(User.id == u_id):
                return jsonify({"error": "User not found"}), 404
            query = query.where(Event.user_id == u_id)
        except ValueError:
            return jsonify({"error": "user_id must be an integer"}), 400

    if url_id is not None:
        try:
            ur_id = int(url_id)
            if not URL.get_or_none(URL.id == ur_id):
                return jsonify({"error": "URL not found"}), 404
            query = query.where(Event.url_id == ur_id)
        except ValueError:
            return jsonify({"error": "url_id must be an integer"}), 400

    query = query.order_by(Event.timestamp.desc())
    total = query.count()

    p_int = int(page) if page else None
    pp_int = int(per_page) if per_page else None

    if p_int and pp_int:
        if p_int < 1 or pp_int < 1 or pp_int > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(p_int, pp_int)

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
            "timestamp": event.timestamp.isoformat(),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": details
        })

    response_data = {"events": result, "total": total}
    if p_int is not None:
        response_data["page"] = p_int
        response_data["per_page"] = pp_int

    return jsonify(response_data), 200


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

    if not url.is_active:
        return jsonify({"error": "URL is inactive"}), 404

    try:
        event = create_event_record(
            event_type=event_type,
            url=url,
            user=user,
            details=details
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