import csv
import io
from datetime import datetime

from flask import Blueprint, request, jsonify
from app.models.user import User

users_bp = Blueprint("users", __name__)


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

        for row in reader:
            username = row["username"].strip()
            email = row["email"].strip()


            does_user_exist = User.get_or_none(
                (User.email == email) | (User.username == username)
            )

            if does_user_exist:
                continue

            User.create(
                username = username,
                email = email, 
            )
            users_imported += 1
        
        return jsonify({"count": users_imported}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@users_bp.route("/users", methods=["GET"])
def list_users():
    users = User.select().dicts()
    return jsonify(list(users)), 200


@users_bp.route("/users/<int:id>", methods=["GET"])
def get_user_by_id(id):
    user = User.get_or_none(User.id == id)

    if not user:
        return jsonify({"error": "user not found"}), 404
    
    print(user)
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at
    }), 200
