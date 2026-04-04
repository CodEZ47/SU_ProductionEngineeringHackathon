import json

from flask import Blueprint, jsonify
from app.models.event import Event

events_bp = Blueprint("events", __name__)

@events_bp.route("/events", methods=["GET"])
def list_events():
    events = Event.select().order_by(Event.timestamp.desc())

    result = []

    for event in events:
        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "url": event.url_id,
            "user": event.user_id,
            "details": json.loads(event.details) if event.details else None
        })

    return jsonify(result), 200


