# ============================================================
# services/study.py — Study Service for Bharat.ai
# ============================================================

from services.model import ask_mistral
from config import SYSTEM_PROMPT


def _ask(prompt: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt}
    ]
    return ask_mistral(messages)


def generate_quiz(topic: str, count: int = 5) -> dict:
    try:
        prompt = f"""Generate {count} multiple choice questions on: {topic}
Format each like this:
Q1. Question here?
a) Option A
b) Option B
c) Option C
d) Option D
Answer: a"""
        return {"success": True, "quiz": _ask(prompt)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_flashcards(topic: str) -> dict:
    try:
        prompt = f"""Generate 10 flashcards for: {topic}
Format each like:
FRONT: Question or term
BACK: Answer or definition
---"""
        return {"success": True, "flashcards": _ask(prompt)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def solve_math(problem: str) -> dict:
    try:
        return {"success": True, "solution": _ask(f"Solve this step by step:\n{problem}")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_essay(topic: str) -> dict:
    try:
        return {"success": True, "essay": _ask(f"Write a well-structured essay on: {topic}\nInclude introduction, main points, and conclusion.")}
    except Exception as e:
        return {"success": False, "error": str(e)}