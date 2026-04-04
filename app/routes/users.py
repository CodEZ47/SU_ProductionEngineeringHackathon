import csv
import io
import re

from flask import Blueprint, request, jsonify
from peewee import IntegrityError, chunked

from app.models.user import User
from app.database import db

users_bp = Blueprint("users", __name__)

def check_input_validity(username, email):
    USERNAME_REGEX = r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$"
    EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if username is not None and (
        not isinstance(username, str) or not re.match(USERNAME_REGEX, username)
    ):
        return jsonify({
            "error": "Invalid username",
            "details": "3-30 chars, letters/numbers/underscore only"
    }), 422

    if email is not None and (
        not isinstance(email, str) or not re.match(EMAIL_REGEX, email)
    ):
        return jsonify({
            "error": "Invalid email",
            "details": "Must be a valid email format"
    }), 422

    return


@users_bp.route("/users/bulk", methods=["POST"])
def import_users_bulk():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    file = request.files["file"]

    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400
    
    try:
        file_content = file.stream.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(file_content))

        users_imported = 0
        rows_to_insert = []
        seen_usernames = set()
        seen_emails = set()

        existing_users = list(User.select(User.username, User.email).dicts())
        existing_usernames = {u["username"] for u in existing_users}
        existing_emails = {u["email"] for u in existing_users}

        for row in reader:
            username = row["username"].strip()
            email = row["email"].strip()

            if (
                username in existing_usernames
                or email in existing_emails
                or username in seen_usernames
                or email in seen_emails
            ):
                continue

            invalid = check_input_validity(username=username, email=email)

            if invalid:
                continue

            rows_to_insert.append({
                "username": username,
                "email": email,
            })

            seen_usernames.add(username)
            seen_emails.add(email)
            users_imported += 1
        
        if not rows_to_insert:
            return jsonify({
                "count":0,
        }), 200

        with db.atomic():
            for batch in chunked(rows_to_insert, 100):
                User.insert_many(batch).execute()
            
        
        return jsonify({"count": users_imported}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@users_bp.route("/users", methods=["POST"])
def create_user():

    data = request.get_json(silent=True) #error is handled by custom handler

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "username and email are required"}), 400
    
    username = username.strip()
    email = email.strip().lower()

    invalid = check_input_validity(username=username, email=email)

    if invalid:
        return invalid

    try:
        user = User.create(username = username, email = email)

        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }), 200
    
    except IntegrityError:
        return jsonify({"error": "User already exists"}), 409


    

@users_bp.route("/users", methods=["GET"])
def list_users():
    users = User.select().dicts()
    resulst = []

    for user in users:
        resulst.append({
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"].isoformat()
        })
    return jsonify(resulst), 200


@users_bp.route("/users/<int:id>", methods=["GET"])
def get_user_by_id(id):
    user = User.get_or_none(User.id == id)

    if not user:
        return jsonify({"error": "user not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }), 200

@users_bp.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "username required"}), 400
    
    user = User.get_or_none(User.id == id)

    if not user:
        return jsonify({"error": "user not found"}), 404
    
    new_username =  data.get("username")

    if not new_username:
        return jsonify({"error": "username requried"}), 400
    
    new_username = new_username.strip()

    invalid = check_input_validity(username=new_username, email=None)

    if invalid:
        return invalid

    user.username = new_username

    try:
        user.save()
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }), 200
    except IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409
