# ============================================================
# routes/learning.py — Multi-Agent Learning Hub for Bharat.ai
# ============================================================

from flask import Blueprint, request, jsonify
from services.model import ask_mistral
import json
import re

learning_bp = Blueprint("learning", __name__)

AGENT_PROMPTS = {
    "teacher": "You are an expert Indian teacher. Explain concepts clearly using relatable Indian examples. Be encouraging and patient. Break down complex topics into simple parts. Use bullet points and structure your answers well.",
    "coding_mentor": "You are a senior software engineer and coding mentor. Help students learn programming with practical code examples, explain time/space complexity, and guide through debugging. Support Python, C++, Java, JavaScript.",
    "exam_coach": "You are an expert exam coach for Indian exams: JEE, NEET, UPSC, CAT, GATE, SSC, and board exams. Give strategic study advice, solve problems, identify high-weightage topics, and provide time management tips.",
    "career_guide": "You are a career counselor with expertise in the Indian job market. Help with career planning, resume building, interview prep, skill gap analysis, and higher education guidance.",
    "research_assistant": "You are an academic research assistant. Help with literature reviews, research methodology, academic writing, project ideas, and report structuring.",
}


@learning_bp.route("/learning/chat", methods=["POST"])
def chat():
    data       = request.get_json() or {}
    message    = data.get("message", "").strip()
    agent_type = data.get("agent_type", "teacher")
    profile    = data.get("profile", {})
    history    = data.get("history", [])

    if not message:
        return jsonify({"error": "No message"}), 400

    system = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["teacher"])

    # Add profile context
    if profile:
        system += f"\n\nStudent Profile: {profile.get('level','')}, {profile.get('classOrCourse','')}, Subjects: {', '.join(profile.get('subjects', []))}"

    messages = [{"role": "system", "content": system}]
    for msg in history[-10:]:
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    try:
        reply = ask_mistral(messages)
        return jsonify({"reply": reply, "agent_type": agent_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@learning_bp.route("/learning/quiz", methods=["POST"])
def generate_quiz():
    data  = request.get_json() or {}
    topic = data.get("topic", "").strip()

    if not topic:
        return jsonify({"error": "No topic"}), 400

    prompt = (
        "Generate exactly 5 multiple choice questions based on this topic. "
        "Return ONLY a valid JSON object with no extra text, no markdown, no code fences.\n"
        'Format: {"questions": [{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct": 0}]}\n'
        "Where correct is 0-based index (0=A, 1=B, 2=C, 3=D).\n\n"
        f"Topic:\n{topic[:500]}"
    )

    messages = [
        {"role": "system", "content": "You are a quiz generator. Return ONLY valid JSON, nothing else."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw = ask_mistral(messages)
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw).strip()
        quiz_data = json.loads(raw)
        questions = quiz_data.get("questions", [])
        validated = [
            {
                "question": str(q.get("question", "")),
                "options":  [str(o) for o in q.get("options", [])[:4]],
                "correct":  int(q.get("correct", 0)),
            }
            for q in questions[:5]
        ]
        return jsonify({"questions": validated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@learning_bp.route("/learning/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Bharat Learning Hub"})