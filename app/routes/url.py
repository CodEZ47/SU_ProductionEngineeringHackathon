from flask import Blueprint, request, jsonify, Response
from datetime import datetime
from urllib.parse import urlparse
import random
import string

from app.models.url import URL
from app.models.user import User
from app.models.event import Event
from app.routes.events import create_event_record

url_bp = Blueprint("urls", __name__)


def serialize_url(url):
    return {
        "id": url.id,
        "user_id": url.user.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.strftime("%Y-%m-%dT%H:%M:%S") if url.created_at else None,
        "updated_at": url.updated_at.strftime("%Y-%m-%dT%H:%M:%S") if url.updated_at else None,
    }


def serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url.id,
        "user_id": event.user.id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        "details": event.details if isinstance(event.details, dict) else {}
    }



def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc


def generate_unique_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not URL.get_or_none(URL.short_code == code):
            return code


def parse_bool(value):
    val = str(value).lower()
    if val in ["true", "1"]:
        return True
    if val in ["false", "0"]:
        return False
    raise ValueError("Invalid boolean")


def get_next_event_id():
    last = Event.select().order_by(Event.id.desc()).first()
    return (last.id + 1) if last else 1



@url_bp.route("/urls", methods=["POST"])
def create_url():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title") or ""

    if user_id is None or original_url is None:
        return jsonify({"error": "user_id and original_url are required"}), 400

    if not isinstance(user_id, int):
        return jsonify({"error": "user_id must be an integer"}), 400

    if not isinstance(original_url, str):
        return jsonify({"error": "original_url must be a string"}), 400

    original_url = original_url.strip()

    if not original_url:
            return jsonify({"error": "original_url cannot be empty"}), 400

    if not is_valid_url(original_url):
        return jsonify({"error": "Invalid URL format"}), 400

    if not isinstance(title, str):
        return jsonify({"error": "title must be a string"}), 400

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "Invalid user_id"}), 400

    existing_url = URL.get_or_none(
        (URL.user_id == user_id) & (URL.original_url == original_url)
    )

    if existing_url:
        if not existing_url.is_active:
            existing_url.is_active = True
            existing_url.updated_at = datetime.utcnow()
            existing_url.save()

            create_event_record(
                event_type="updated",
                url=existing_url,
                user=user,
                details={"short_code": existing_url.short_code, "original_url": original_url}
            )
        return jsonify(serialize_url(existing_url)), 200

    now = datetime.utcnow()
    code = generate_unique_code()

    new_url = URL.create(
        user=user,
        short_code=code,
        original_url=original_url,
        title=title,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    create_event_record(
        event_type="created",
        url=new_url,
        user=user,
        details={"short_code": code, "original_url": original_url}
    )

    return jsonify(serialize_url(new_url)), 201


@url_bp.route("/urls", methods=["GET"])
def get_urls():
    query = URL.select()

    user_id = request.args.get("user_id")
    is_active = request.args.get("is_active")

    if user_id:
        try:
            query = query.where(URL.user_id == int(user_id))
        except ValueError:
            return jsonify({"error": "Invalid user_id"}), 400

    if is_active is not None:
        try:
            query = query.where(URL.is_active == parse_bool(is_active))
        except ValueError:
            return jsonify({"error": "Invalid is_active"}), 400

    # pagination support
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    if page and per_page:
        try:
            page = int(page)
            per_page = int(per_page)
            offset = (page - 1) * per_page
            query = query.limit(per_page).offset(offset)
        except ValueError:
            return jsonify({"error": "Invalid pagination params"}), 400
    elif "limit" in request.args or "offset" in request.args:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        query = query.limit(limit).offset(offset)

    return jsonify([serialize_url(u) for u in query]), 200


@url_bp.route("/urls/<int:id>", methods=["GET"])
def get_url_by_id(id):
    url = URL.get_or_none(URL.id == id)

    if not url:
        return jsonify({"error": "URL not found"}), 404

    return jsonify(serialize_url(url)), 200


@url_bp.route("/urls/<int:id>", methods=["PUT"])
def update_url(id):
    url = URL.get_or_none(URL.id == id)

    if not url:
        return jsonify({"error": "URL not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    updated_fields = []

    if "title" in data:
        if not isinstance(data["title"], str):
            return jsonify({"error": "title must be a string"}), 400
        if len(data["title"]) > 255:
            return jsonify({"error": f"title must be at most {255} characters"}), 422
        url.title = data["title"]
        updated_fields.append("title")

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        url.is_active = data["is_active"]
        updated_fields.append("is_active")

    url.updated_at = datetime.utcnow()
    url.save()

    create_event_record(
        event_type="updated",
        url=url,
        user=url.user,
        details={"updated_fields": updated_fields}
    )

    return jsonify(serialize_url(url)), 200


@url_bp.route("/urls/<int:id>", methods=["DELETE"])
def delete_url(id):
    url = URL.get_or_none(URL.id == id)

    if not url:
        return jsonify({"error": "URL not found"}), 404

    now = datetime.utcnow()


    try:
        create_event_record(
            event_type="deleted",
            url=url,
            user=url.user,
            details={"short_code": url.short_code, "original_url": url.original_url}
        )
    except Exception as e:
        print("Event logging failed:", e)


    Event.delete().where(Event.url_id == id).execute()

    url.delete_instance()

    return jsonify({"message": "URL removed"}), 204


@url_bp.route("/<string:short_code>", methods=["GET"])
def redirect_short_code(short_code):
    url = URL.get_or_none(URL.short_code == short_code)


    if not url:
        return jsonify({"error": "URL not found"}), 404
    
    if not url.is_active:
        create_event_record(
            url=url,
            user=url.user,
            event_type="visited",
            details={"short_code": short_code}
        )
        return jsonify({"error": "URL is inactive"}), 410
    
    if not url.user:
        return jsonify({"error": "URL owner not found"}), 404

    create_event_record(
        url=url,
        user=url.user,
        event_type="visited",
        details={"short_code": short_code}
    )

    return Response("", status=302, headers={"Location": url.original_url})