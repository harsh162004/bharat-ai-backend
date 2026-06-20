# language.py — Indian Language Detector for Bharat AI

from lingua import Language, LanguageDetectorBuilder

_detector = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.HINDI,
    Language.BENGALI,
    Language.GUJARATI,
    Language.PUNJABI,
    Language.TAMIL,
    Language.TELUGU,
    Language.URDU,
    Language.MARATHI,
).build()

LINGUA_MAP = {
    Language.ENGLISH:   "english",
    Language.HINDI:     "hindi",
    Language.BENGALI:   "bengali",
    Language.GUJARATI:  "gujarati",
    Language.PUNJABI:   "punjabi",
    Language.TAMIL:     "tamil",
    Language.TELUGU:    "telugu",
    Language.URDU:      "urdu",
    Language.MARATHI:   "marathi",
}

def detect_language(text: str) -> str:
    detected = _detector.detect_language_of(text)
    if detected in LINGUA_MAP:
        return LINGUA_MAP[detected]
    return "english"

def get_language_instruction(text: str) -> str:
    lang = detect_language(text)

    if lang == "english":
        return "REPLY IN ENGLISH ONLY."

    elif lang == "hindi":
        return "REPLY IN HINDI ONLY."

    elif lang == "bengali":
        return "REPLY IN BENGALI ONLY."

    elif lang == "tamil":
        return "REPLY IN TAMIL ONLY."

    elif lang == "telugu":
        return "REPLY IN TELUGU ONLY."

    elif lang == "marathi":
        return "REPLY IN MARATHI ONLY."

    elif lang == "gujarati":
        return "REPLY IN GUJARATI ONLY."

    elif lang == "punjabi":
        return "REPLY IN PUNJABI ONLY."

    elif lang == "malayalam":
        return "REPLY IN MALAYALAM ONLY."

    elif lang == "kannada":
        return "REPLY IN KANNADA ONLY."

    elif lang == "urdu":
        return "REPLY IN URDU ONLY."

    return "REPLY IN ENGLISH ONLY."