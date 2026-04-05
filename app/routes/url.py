from flask import Blueprint, request, jsonify, redirect, Response
from datetime import datetime
import json

from app.models.url import URL
from app.models.user import User
from app.models.event import Event

url_bp = Blueprint("urls", __name__)


def serialize_url(url):
    return {
        "id": url.id,
        "user_id": url.user.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }



@url_bp.route("/urls", methods=["POST"])
def create_url():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title")

    if user_id is None or original_url is None:
        return jsonify({"error": "user_id and original_url are required"}), 400

    if not isinstance(user_id, int):
        return jsonify({"error": "user_id must be an integer"}), 400

    if not isinstance(original_url, str):
        return jsonify({"error": "original_url must be a string"}), 400

    if title is not None and not isinstance(title, str):
        return jsonify({"error": "title must be a string"}), 400

    original_url = original_url.strip()

    if original_url == "":
        return jsonify({"error": "original_url cannot be empty"}), 400

    if len(original_url) > 2048:
        return jsonify({"error": "URL too long"}), 400

    if title and len(title) > 255:
        return jsonify({"error": "title too long"}), 400

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    now = datetime.utcnow()

    # simple short code generator (replace if needed)
    import random, string
    def generate_code(length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    code = generate_code()

    try:
        new_url = URL.create(
            user=user,
            short_code=code,
            original_url=original_url,
            title=title,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Safe event logging
    try:
        Event.create(
            url=new_url,
            user=user,
            event_type="created",
            timestamp=now,
            details=json.dumps({
                "short_code": code,
                "original_url": original_url
            })
        )
    except Exception as e:
        print("Event logging failed:", e)

    return jsonify(serialize_url(new_url)), 201


@url_bp.route("/urls", methods=["GET"])
def get_urls():
    query = URL.select()

    user_id = request.args.get("user_id")
    is_active = request.args.get("is_active")

    if user_id:
        try:
            query = query.where(URL.user == int(user_id))
        except:
            return jsonify({"error": "Invalid user_id"}), 400

    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.where(URL.is_active == is_active_bool)

    urls = [serialize_url(u) for u in query]

    return jsonify(urls), 200



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

    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    if "title" in data:
        if not isinstance(data["title"], str):
            return jsonify({"error": "title must be a string"}), 400
        url.title = data["title"]

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        url.is_active = data["is_active"]

    url.updated_at = datetime.utcnow()
    url.save()

    return jsonify(serialize_url(url)), 200




@url_bp.route("/urls/<int:id>", methods=["DELETE"])
def delete_url(id):
    url = URL.get_or_none(URL.id == id)

    if not url:
        return jsonify({"error": "URL not found"}), 404

    Event.delete().where(Event.url == url).execute()

    url.delete_instance()

    return "", 204



@url_bp.route("/<string:short_code>", methods=["GET"])
def redirect_short_code(short_code):
    url = URL.get_or_none(URL.short_code == short_code)

    if not url or not url.is_active:
        return jsonify({"error": "URL not found or inactive"}), 404

    return Response(status=302, headers={
        "Location": url.original_url
    })