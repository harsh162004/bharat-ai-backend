# ============================================================
# services/voice.py — Voice Service for Bharat.ai
# ============================================================

import re
import os
from groq import Groq
from config import ENGINE_A_KEY


# ── Clean text for speech ─────────────────────────────────────
def clean_for_speech(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Text to Speech ────────────────────────────────────────────
def speak(text: str) -> dict:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 1.0)

        # Try to set an Indian English voice
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'india' in voice.name.lower() or 'indian' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break

        engine.say(text)
        engine.runAndWait()
        return {"success": True, "message": "Speech completed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Speech to Text ────────────────────────────────────────────
def listen(audio_file_path: str) -> dict:
    """
    Transcribe audio file using Groq Whisper.
    audio_file_path: path to the uploaded audio file (webm/wav/etc)
    """
    if not audio_file_path or not os.path.exists(audio_file_path):
        return {"success": False, "error": "No audio file provided"}

    try:
        client = Groq(api_key=ENGINE_A_KEY)
        with open(audio_file_path, "rb") as f:
           result = client.audio.transcriptions.create(
    model="whisper-large-v3-turbo",
    file=f,
    language="en",
    prompt="This is a question asked to an AI assistant about Indian education, universities, or general knowledge."
)
        return {"success": True, "text": result.text}
    except Exception as e:
        return {"success": False, "error": str(e)}