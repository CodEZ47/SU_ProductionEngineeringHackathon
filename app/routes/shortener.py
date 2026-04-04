from flask import Blueprint, request, jsonify, redirect
from app.models.short_url import ShortURL, generate_code

shortener_bp = Blueprint("shortener", __name__)
@shortener_bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]

    # generate unique code
    while True:
        code = generate_code()
        exists = ShortURL.select().where(ShortURL.short_code == code).exists()
        if not exists:
            break

    short = ShortURL.create(
        original_url=url,
        short_code=code
    )

    return jsonify({
        "original_url": short.original_url,
        "short_code": short.short_code,
        "short_url": f"http://localhost:5000/{short.short_code}"
    })
@shortener_bp.route("/<code>")
def redirect_url(code):
    try:
        short = ShortURL.get(ShortURL.short_code == code)

        # increment click count
        short.click_count += 1
        short.save()

        return redirect(short.original_url)

    except ShortURL.DoesNotExist:
        return jsonify({"error": "Short URL not found"}), 404
    
