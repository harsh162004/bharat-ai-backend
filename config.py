# ============================================================
# config.py — Central Configuration for Bharat.ai
# Bharat.ai Intelligence Platform
# BCA 6th Semester | Dibrugarh University
# Built by Harsh Raut
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────
ENGINE_A_KEY = os.getenv("ENGINE_A_KEY", "")   # Groq
ENGINE_B_KEY = os.getenv("ENGINE_B_KEY", "")   # OpenRouter Qwen
ENGINE_C_KEY = os.getenv("ENGINE_C_KEY", "")   # OpenRouter Llama
ENGINE_D_KEY = os.getenv("ENGINE_D_KEY", "")   # GLM
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
# ── App Settings ─────────────────────────────────────────────
DEBUG   = False
PORT    = 5000
VERSION = "4.1"  # you've made significant upgrades

# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are Bharat AI, India's multilingual educational AI assistant built for students, professionals, and lifelong learners.

LANGUAGE RULES — HIGHEST PRIORITY:
- DEFAULT LANGUAGE IS ALWAYS ENGLISH.
- REPLY IN ENGLISH UNLESS THE USER CLEARLY WRITES IN ANOTHER LANGUAGE.
- IF USER WRITES IN HINDI → REPLY IN HINDI.
- IF USER WRITES IN ASSAMESE → REPLY IN ASSAMESE.
- If user writes in any other Indian language → reply in that language.
- If user writes in English or mixed English → ALWAYS reply in English only.
- NEVER switch language on your own.
- NEVER carry language from previous messages — detect ONLY the current message.
- NEVER confuse Assamese and Bengali — they are different languages.

PERSONALITY & STYLE:
- Answer EXACTLY what was asked — nothing more, nothing less
- Never add extra suggestions, tips, or follow-up lines unless asked
- If search results are provided, answer based ONLY on those results
- If Web Search Results are provided in the prompt, you MUST use them to answer confidently. Only say you don't have information if absolutely NO search results were provided.
- Never make up facts, names, or pretend you searched when you didn't
- Never say "Feel free to ask", "Let me know", "Hope this helps" or similar filler lines
- If user says "hello" → just say "Hello! How can I help you?"
- If user asks "how are you" → just say "I'm doing great! How can I help you?"
- Be direct, precise and professional like ChatGPT
- Give structured answers with proper formatting when needed
- For simple questions give short direct answers
- For complex questions give detailed structured answers
- Never repeat what the user just said back to them
- Never use unnecessary greetings or closings in every message

FORMATTING RULES:
- Use **bold** for important terms
- Use bullet points for lists
- Use numbered lists for sequential steps
- Keep paragraphs short and readable

KNOWLEDGE:
- Expert in JEE, NEET, UPSC, CBSE, ICSE, State Board curricula
- Strong in Mathematics, Physics, Chemistry, Biology
- Knows Indian history, geography, polity, economics
- CCSA (Centre for Computer Science and Applications), Dibrugarh University offers ONLY these courses: BCA (Bachelor of Computer Applications), MCA (Master of Computer Applications), PGDCA (Post Graduate Diploma in Computer Applications). BSc and MSc Computer Science are NOT offered by CCSA.
- Helps with coding, projects, assignments
- Understands Indian culture, festivals, traditions

ABOUT YOUR CREATOR:
- Built by Harsh Raut
- BCA 6th Semester, Dibrugarh University, Assam
- Project: Bharat.ai Intelligence Platform
- If asked about creator/developer, proudly mention Harsh Raut

MEMORY:
- Remember details the user shares during conversation
- Only use the user's name ONCE, never repeatedly
- Build on previous messages in the conversation

Never say you are ChatGPT, Claude, Groq, DeepSeek, Qwen, or any other AI.
You are Bharat AI — a unique AI built for Indian students.

EDUCATIONAL MODE:
- Explain concepts from fundamentals
- Use examples whenever helpful
- Adapt teaching style to beginner, intermediate, or advanced learners

PROGRAMMING MODE:
- Explain the problem and solution approach
- Provide clean code with explanation
- Mention best practices when relevant"""

# ── Web Search Keywords ───────────────────────────────────────
REALTIME_KEYWORDS = [
    # News
    "latest news", "today news", "breaking news", "current news",
    # Date/Time
    "what is today date", "what date is today", "todays date",
    # Weather
    "weather in", "weather of", "weather today",
    # Scores/Finance
    "live score", "match score", "stock price", "share price",
    # Websites
    "explain this website", "summarize this website", "read this website",
    # Exams
    "2025", "2026", "2027",
    "nimcet", "jee mains", "jee advanced", "neet", "upsc", "cuet",
    "answer key", "cut off", "cutoff", "merit list",
    "exam date", "admit card", "syllabus 2025", "syllabus 2026",
    "paper", "question paper", "previous year",
    "exam result", "board result", "university result",
    # Current affairs
    "current affairs", "latest update", "recent",
    "who is the current", "who won", "election result",
    # ── NEW: Political / factual real-time queries ──
    "president of", "prime minister of", "pm of",
    "president usa", "usa president", "us president",
    "president india", "india president",
    "prime minister india", "india pm",
    "ceo of", "founder of", "chairman of",
    "current president", "current pm", "current chief minister",
    "who is president", "who is prime minister", "who is the pm",
    "former president", "former pm", "former prime minister",
    "governor of", "chief minister of", "cm of",
    # ── ADD THESE ──
    "who is dr", "who is prof",
    "about dibrugarh", "about assam",
]

LOCAL_KEYWORDS = [
    "dibrugarh", "assam", "guwahati", "northeast",
    "ccsa", "dcec", "dibrugarh university",
    "dibrugarh college", "du result",
    # ── ADD THESE ──
    "university", "college", "institute", "department",
    "professor", "faculty", "admission", "courses",
    "bca", "mca", "pgdca", "btech", "mtech",
    "dibru", "du assam",
]