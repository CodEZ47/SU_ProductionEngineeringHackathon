import json

from flask import Blueprint, jsonify
from app.models.event import Event

events_bp = Blueprint("events", __name__)

@events_bp.route("/events", methods=["GET"])
def list_events():
    events = Event.select().order_by(Event.timestamp.desc())

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


