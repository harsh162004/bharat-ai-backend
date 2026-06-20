# ============================================================
# routes/study.py — Study Routes for Bharat.ai
# ============================================================

from flask import Blueprint, request, jsonify
from services.study import generate_quiz, generate_flashcards, solve_math, generate_essay

study_bp = Blueprint("study", __name__)


# ── POST /generate-quiz ───────────────────────────────────────
@study_bp.route("/generate-quiz", methods=["POST"])
def quiz():
    data    = request.json or {}
    topic   = data.get("topic", "").strip()
    count   = data.get("count", 5)
    if not topic:
        return jsonify({"success": False, "error": "No topic provided"}), 400
    result = generate_quiz(topic, count)
    return jsonify(result)


# ── POST /generate-flashcards ─────────────────────────────────
@study_bp.route("/generate-flashcards", methods=["POST"])
def flashcards():
    data  = request.json or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"success": False, "error": "No topic provided"}), 400
    result = generate_flashcards(topic)
    return jsonify(result)


# ── POST /solve-math ──────────────────────────────────────────
@study_bp.route("/solve-math", methods=["POST"])
def math():
    data     = request.json or {}
    problem  = data.get("problem", "").strip()
    if not problem:
        return jsonify({"success": False, "error": "No problem provided"}), 400
    result = solve_math(problem)
    return jsonify(result)


# ── POST /generate-essay ──────────────────────────────────────
@study_bp.route("/generate-essay", methods=["POST"])
def essay():
    data  = request.json or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"success": False, "error": "No topic provided"}), 400
    result = generate_essay(topic)
    return jsonify(result)