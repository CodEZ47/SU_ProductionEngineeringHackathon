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


def create_event_record(event_type, url, user, details=None):
    if details is not None and not isinstance(details, dict):
        raise ValueError("Details must be a JSON object")
    event = Event.create(
        id=get_next_event_id(),
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

    query = (Event
             .select(Event, URL)
             .join(URL)
             .where(URL.is_active == True))

    if event_type:
        query = query.where(Event.event_type == event_type)

    if user_id is not None:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"error": "user_id must be an integer"}), 400
        query = query.where(Event.user_id == user_id)

    if url_id is not None:
        try:
            url_id = int(url_id)
        except ValueError:
            return jsonify({"error": "url_id must be an integer"}), 400
        query = query.where(Event.url_id == url_id)

    query = query.order_by(Event.timestamp.desc())
    total = query.count()

    use_pagination = page is not None and per_page is not None

    if use_pagination:
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError:
            return jsonify({"error": "page and per_page must be integers"}), 400

        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400

        max_page = (total + per_page - 1) // per_page if total > 0 else 1
        if page > max_page:
            events = []
            result = []
            response_page = page
            response_per_page = per_page
        else:
            query = query.paginate(page, per_page)
            events = query
            result = []
            for event in events:
                details = None
                if event.details:
                    if isinstance(event.details, str):
                        try:
                            details = json.loads(event.details)
                        except (json.JSONDecodeError, TypeError):
                            details = event.details
                    else:
                        details = event.details
                result.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "url_id": event.url_id,
                    "user_id": event.user_id,
                    "details": details
                })
            response_page = page
            response_per_page = per_page
    else:
        events = query
        result = []
        for event in events:
            details = None
            if event.details:
                if isinstance(event.details, str):
                    try:
                        details = json.loads(event.details)
                    except (json.JSONDecodeError, TypeError):
                        details = event.details
                else:
                    details = event.details
            result.append({
                "id": event.id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "url_id": event.url_id,
                "user_id": event.user_id,
                "details": details
            })
        response_page = None
        response_per_page = None

    response_data = {"events": result, "total": total}
    if use_pagination and response_page is not None:
        response_data["page"] = response_page
        response_data["per_page"] = response_per_page

    return jsonify(response_data), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)

    if not data or data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    event_type = data.get("event_type")
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    details = data.get("details")

    if event_type is None or url_id is None or user_id is None:
        missing = []
        if event_type is None: missing.append("event_type")
        if url_id is None: missing.append("url_id")
        if user_id is None: missing.append("user_id")
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not isinstance(user_id, int) or not isinstance(url_id, int):
        return jsonify({"error": "user_id and url_id must be integers"}), 400

    if not isinstance(event_type, str) or len(event_type.strip()) == 0:
        return jsonify({"error": "event_type must be a non-empty string"}), 400

    if details is not None and not isinstance(details, dict):
        return jsonify({"error": "Details must be a JSON object"}), 400

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404

    url = URL.get_or_none((URL.id == url_id) & (URL.is_active == True))
    if not url:
        return jsonify({"error": f"URL with id {url_id} not found or inactive"}), 404

    try:
        event = create_event_record(
            event_type=event_type.strip(),
            url=url,
            user=user,
            details=details
        )

        response_details = details if details is not None else None

        return jsonify({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "url_id": event.url_id,
            "user_id": event.user_id,
            "details": response_details
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500