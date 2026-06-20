# ============================================================
# routes/voice.py — Voice Routes for Bharat.ai
# ============================================================

import tempfile
import os
from flask import Blueprint, request, jsonify
from services.voice import speak, listen, clean_for_speech

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/voice/speak", methods=["POST"])
def voice_speak():
    data    = request.json or {}
    text    = data.get("text", "")
    cleaned = clean_for_speech(text)
    result  = speak(cleaned)
    return jsonify(result)


@voice_bp.route("/voice/listen", methods=["POST"])
def voice_listen():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file uploaded"}), 400

    audio_file = request.files["audio"]

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = listen(tmp_path)
        return jsonify(result)
    finally:
        os.unlink(tmp_path)