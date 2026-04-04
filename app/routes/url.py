from flask import Blueprint, request, jsonify
from datetime import datetime
import random
import string
from urllib.parse import urlparse

from app.models.url import URL
from app.models.user import User
from app.models.event import Event

from flask import redirect


url_bp = Blueprint("url", __name__)


def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_unique_code():
    while True:
        code = generate_code()
        if not URL.select().where(URL.short_code == code).exists():
            return code


def is_valid_url(url):
    if not isinstance(url, str):
        return False

    url = url.strip()

    # MUST start with http/https
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    try:
        parsed = urlparse(url)
        return bool(parsed.netloc and "." in parsed.netloc)
    except:
        return False


@url_bp.route("/urls", methods=["POST"])
def create_url():
    data = request.get_json(force=True, silent=True)



    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title")

    print("original_url:", original_url)  # debug

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

    if not is_valid_url(original_url):
        return jsonify({"error": "Invalid URL format"}), 400

    if len(original_url) > 2048:
        return jsonify({"error": "URL too long"}), 400

    if title and len(title) > 255:
        return jsonify({"error": "title too long"}), 400

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    now = datetime.utcnow()
    code = generate_unique_code()

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

    try:
        Event.create(
            user=user,
            url=new_url,
            event_type="created",
            timestamp=now,
            details={
                "short_code": code,
                "original_url": original_url
            }
        )
    except Exception as e:
        print("Event logging failed:", e)

    return jsonify({
        "id": new_url.id,
        "user_id": new_url.user.id,
        "short_code": new_url.short_code,
        "original_url": new_url.original_url,
        "title": new_url.title,
        "is_active": new_url.is_active,
        "created_at": new_url.created_at.isoformat(),
        "updated_at": new_url.updated_at.isoformat(),
    }), 201



@url_bp.route("/urls", methods=["GET"])
def list_urls():
    user_id = request.args.get("user_id")
    is_active = request.args.get("is_active")
    short_code = request.args.get("short_code")

    query = URL.select()

    if user_id is not None:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"error": "user_id must be an integer"}), 400
        query = query.where(URL.user == user_id)

    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.where(URL.is_active == is_active_bool)

    if short_code is not None:
        query = query.where(URL.short_code == short_code)

    urls = []
    for url in query:
        urls.append({
            "id": url.id,
            "user_id": url.user.id,
            "short_code": url.short_code,
            "original_url": url.original_url,
            "title": url.title,
            "is_active": url.is_active,
            "created_at": url.created_at.isoformat(),
            "updated_at": url.updated_at.isoformat(),
        })

    return jsonify(urls), 200

from flask import Blueprint, jsonify
from app.models import URL  # adjust import if needed

url_bp = Blueprint('urls', __name__)


@url_bp.route('/urls/<int:id>', methods=['GET'])
def get_url_by_id(id):
    url = URL.get_or_none(URL.id == id)

    if not url:
        return jsonify({"error": "URL not found"}), 404

    return jsonify({
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None
    }), 200