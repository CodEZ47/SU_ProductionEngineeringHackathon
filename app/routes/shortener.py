import random
import string
from datetime import datetime

from flask import Blueprint, request, jsonify, redirect
from peewee import fn

from app.models.url import URL
from app.models.event import Event
from app.models.user import User

shortener_bp = Blueprint("shortener", __name__)


def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def next_url_id():
    max_id = URL.select(fn.MAX(URL.id)).scalar()
    return 1 if max_id is None else max_id + 1


def next_event_id():
    max_id = Event.select(fn.MAX(Event.id)).scalar()
    return 1 if max_id is None else max_id + 1


@shortener_bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    original_url = data["url"]
    user_id = data.get("user_id", 1)
    title = data.get("title")
    now = datetime.now()

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    while True:
        code = generate_code()
        exists = URL.select().where(URL.short_code == code).exists()
        if not exists:
            break

    new_url = URL.create(
        id=next_url_id(),
        user=user,
        short_code=code,
        original_url=original_url,
        title=title,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    Event.create(
        id=next_event_id(),
        url=new_url,
        user=user,
        event_type="created",
        timestamp=now,
        details="Short URL created"
    )

    return jsonify({
        "id": new_url.id,
        "original_url": new_url.original_url,
        "short_code": new_url.short_code,
        "short_url": f"http://localhost:5000/{new_url.short_code}",
        "user_id": user.id,
        "title": new_url.title,
        "is_active": new_url.is_active
    }), 201


@shortener_bp.route("/<code>", methods=["GET"])
def redirect_url(code):
    try:
        url_entry = URL.get(URL.short_code == code)
    except URL.DoesNotExist:
        return jsonify({"error": "Short URL not found"}), 404

    if not url_entry.is_active:
        return jsonify({"error": "Short URL is inactive"}), 410

    Event.create(
        id=next_event_id(),
        url=url_entry,
        user=url_entry.user,
        event_type="clicked",
        timestamp=datetime.now(),
        details="Short URL visited"
    )

    return redirect(url_entry.original_url)