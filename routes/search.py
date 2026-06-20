# ============================================================
# routes/search.py — Search Routes for Bharat.ai
# ============================================================

from flask import Blueprint, request, jsonify
from services.search import web_search

search_bp = Blueprint("search", __name__)


# ── POST /web-search ──────────────────────────────────────────
@search_bp.route("/web-search", methods=["POST"])
def search():
    data  = request.json or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"success": False, "error": "No query provided"}), 400

    result = web_search(query)
    return jsonify(result)