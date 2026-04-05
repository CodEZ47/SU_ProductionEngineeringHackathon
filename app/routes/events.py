import json

from flask import Blueprint, jsonify, request
from app.models.event import Event

events_bp = Blueprint("events", __name__)

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

    if page is not None and per_page is not None:
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError:
            return jsonify({"error": "page and per_page must be integers"}), 400
    
        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        query = query.paginate(page, per_page)
    

    events = query

    result = []

    for event in events:
        details = None
        if event.details:
            try:
                details = json.loads(event.details)
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

    return jsonify(result), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True) #error is handled by custom handler

    if not data or data is None:
        return jsonify({"error": "Invalid JSON"}), 400
    
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    
    event_type = data.get("event_type")
    url_id = data.get("url_id")
    user_id = data.get("user_id")
    details = data.get("details")

    if not event_type or not url_id or not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        event = Event.create(
            event_type=event_type,
            url_id=url_id,
            user_id=user_id,
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

