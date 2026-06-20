# ============================================================
# app.py — Bharat.ai Flask API Entry Point v4.0
# BCA 6th Semester | Dibrugarh University
# Built by Harsh Raut & Shanu Das
# ============================================================

from flask import Flask, jsonify
from flask_cors import CORS

from config import PORT, VERSION, DEBUG

# ── Import Blueprints ─────────────────────────────────────────
from routes.chat   import chat_bp
from routes.voice  import voice_bp
from routes.search import search_bp
from routes.study  import study_bp
from routes.learning import learning_bp
# ── Create App ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── Register Blueprints ───────────────────────────────────────
app.register_blueprint(chat_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(search_bp)
app.register_blueprint(study_bp)
app.register_blueprint(learning_bp) 

# ── Health Check ──────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":      "running",
        "platform":    "Bharat.ai Intelligence",
        "version":     VERSION,
        "developer":   "Harsh Raut & Shanu Das",
        "university":  "Dibrugarh University"
    })

@app.route("/test-models", methods=["GET"])
def test_models():
    from services.model import _gok, _ook, _gemini_ok
    return jsonify({
        "groq": _gok,
        "openrouter": _ook,
        "gemini": _gemini_ok,
    })
# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print(f"  🇮🇳  Bharat.ai Intelligence Platform v{VERSION}")
    print("  BCA 6th Sem | Dibrugarh University")
    print("  Built by Harsh Raut & Shanu Das")
    print("=" * 50)
    print(f"🌐  Server  →  http://localhost:{PORT}")
    print("=" * 50)
    app.run(port=PORT, debug=DEBUG)