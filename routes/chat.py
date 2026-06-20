# ============================================================
# routes/chat.py — Chat Routes for Bharat.ai (FIXED v2.2)
# ============================================================

from flask import Blueprint, request, jsonify, Response
import json
import time
import re

from config import SYSTEM_PROMPT, REALTIME_KEYWORDS, LOCAL_KEYWORDS
from services.model  import ask_mistral, ask_mistral_stream
from services.memory import get_memory, add_to_memory, build_messages_with_memory, get_all_chats, delete_chat, rename_chat
from services.search import combined_search
from services.image  import generate_image, is_image_request, extract_image_prompt
from services.executor import execute_code, extract_code, is_code_request, is_safe_code

chat_bp = Blueprint("chat", __name__)


def needs_web_search(message: str) -> bool:
    msg = message.lower().strip()

    self_identity = [
        "who are you", "what are you", "who built you", "who made you",
        "who created you", "what is your name", "introduce yourself"
    ]
    for phrase in self_identity:
        if phrase in msg:
            return False

    if "http://" in msg or "https://" in msg:
        return True

    for kw in REALTIME_KEYWORDS:
        if kw in msg:
            return True

    for kw in LOCAL_KEYWORDS:
        if kw in msg:
            return True

    if re.search(r'\b(details|about|information|tell me about|explain)\b', msg):
        return True

    if re.search(r'\bwho\s+(is|was|are|were)\b', msg):
        return True

    if re.search(r'\b(president|prime minister|pm|ceo|chairman|governor|chief minister|cm|minister)\b', msg):
        return True

    if re.search(r'\b(current|latest|new|recent|today|now|2024|2025|2026)\b', msg):
        return True

    if re.search(r'\b(former|previous|last|ex-|ex )\b', msg):
        return True

    return False


def _has_pronoun(message: str) -> bool:
    pronouns = ["he", "she", "they", "him", "her", "his", "their", "it", "this", "that", "they're", "he's", "she's"]
    words = re.findall(r'\b\w+\b', message.lower())
    return any(p in words for p in pronouns)


def _resolve_pronoun(message: str, session_id: str) -> str:
    if not _has_pronoun(message):
        return message
    
    memory = get_memory(session_id)
    if not memory or len(memory) < 2:
        return message
    
    last_user_msgs = [m for m in memory if m.get("role") == "user"]
    if len(last_user_msgs) < 2:
        return message
    
    last_user_msg = last_user_msgs[-2].get("content", "")
    if not last_user_msg or _has_pronoun(last_user_msg):
        for msg in reversed(last_user_msgs[:-2]):
            if not _has_pronoun(msg.get("content", "")):
                last_user_msg = msg.get("content", "")
                break
    
    if not last_user_msg:
        return message
    
    expanded = f"{last_user_msg}. {message}"
    print(f"🔄 Pronoun resolved: '{message}' → '{expanded[:100]}...'")
    return expanded


# Role/title words. Questions containing these ("who is the president of the
# usa", "who is the CEO of Tesla") are asking who currently holds a position —
# NOT asking us to verify one specific named individual. They need to be
# treated differently from person-name lookups ("who is Harish Sharma") at
# every stage: the early-exit confidence check AND the instructions we hand
# the AI, otherwise either layer can independently refuse to answer just
# because the question's wording doesn't appear verbatim in the results.
ROLE_KEYWORDS = [
    "president", "prime minister", "pm", "ceo", "chairman",
    "governor", "chief minister", "cm", "minister", "king",
    "queen", "captain", "founder", "owner", "mayor", "director",
    "head of", "secretary", "speaker", "judge", "justice",
]


def _is_role_query(query: str) -> bool:
    q = query.lower()
    return any(role in q for role in ROLE_KEYWORDS)


def _is_low_confidence_result(web_context: str, query: str) -> bool:
    """Detect when search results don't actually match the queried person/entity."""
    if not web_context or web_context == "No results found.":
        return True

    name_match = re.search(r'who\s+(?:is|was|are|were)\s+(.+)', query.lower())
    if not name_match:
        return False

    name = name_match.group(1).strip()
    # Strip trailing punctuation (e.g. the "?" in "who is the president of the usa ?")
    # so it doesn't break the substring match below.
    name = re.sub(r'[?!.]+$', '', name).strip()

    # Skip the strict verbatim check for role/title questions — see ROLE_KEYWORDS comment above.
    if any(role in name for role in ROLE_KEYWORDS):
        return False

    name_parts = name.split()
    context_lower = web_context.lower()

    # Full name must appear in results
    full_name = " ".join(name_parts)
    if full_name not in context_lower:
        return True

    return False
def _context_is_relevant(web_context: str, query: str) -> bool:
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    context_lower = web_context.lower()
    matches = sum(1 for w in query_words if w in context_lower)
    return matches >= 1

def build_search_prompt(user_message: str, web_context: str, conversation_context: str = "") -> list:
    if _is_role_query(user_message):
        # Relaxed instructions: just read the results and answer who holds the
        # role. No "exact phrase must match" requirement — the results will
        # almost never echo the question's exact wording (e.g. "President of
        # the United States" vs. "president of the usa"), so demanding a
        # literal match here just makes the AI refuse to answer good results.
        instructions = (
            "- Answer ONLY from the search results above.\n"
            "- Identify who currently holds this position based on the search results, "
            "even if the wording differs slightly from the question (e.g. 'usa' vs 'United States').\n"
            "- Your FIRST sentence must directly state the FULL name and the role/fact.\n"
            "- ALWAYS use the person's complete full name — never just a first name.\n"
            "- Example: 'The current Chief Minister of Assam is Himanta Biswa Sarma (since May 2021).'\n"
            "- Only say you couldn't find the answer if the results genuinely don't mention "
            "anyone holding this role.\n"
            "- Use ONLY facts explicitly stated in the results."
        )
    else:
        # Strict instructions: used for specific person-name lookups, where the
        # real risk is mixing up two different people with similar names.
        instructions = (
            "- Answer ONLY from the search results above.\n"
            "- If the exact person/entity in the question is NOT clearly in the results, "
            "say: 'I could not find reliable information about this person.'\n"
            "- NEVER guess, infer, or combine unrelated people's info.\n"
            "- Do NOT mix up similar names (e.g. 'Harish' vs 'Harsh').\n"
            "- Your FIRST sentence must directly state the FULL name and fact.\n"
            "- ALWAYS use the person's complete full name — never just a first name.\n"
            "- Example: 'The current Chief Minister of Assam is Himanta Biswa Sarma (since May 2021).'\n"
            "- For factual/role questions: state the answer directly in the first sentence.\n"
            "- For general information questions: give a complete structured answer.\n"
            "- Use ONLY facts explicitly stated in the results.\n"
            "- Synthesize a clear, direct answer from the search results provided."
        )

    content = (
        f"Question: {user_message}\n\n"
        f"{conversation_context}"
        f"Web Search Results:\n{web_context}\n\n"
        "Instructions:\n"
        f"{instructions}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ]


def build_conversation_context(memory: list, max_messages: int = 4) -> str:
    if not memory or len(memory) < 2:
        return ""
    
    recent = memory[-max_messages:]
    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            short = content[:200] + "..." if len(content) > 200 else content
            lines.append(f"Assistant: {short}")
    
    if lines:
        return "Recent Conversation:\n" + "\n".join(lines) + "\n\n"
    return ""


@chat_bp.route("/chats", methods=["GET"])
def get_chats():
    return jsonify({"chats": get_all_chats()})


@chat_bp.route("/chat-history/<session_id>", methods=["GET"])
def chat_history(session_id):
    return jsonify({"messages": get_memory(session_id)})


@chat_bp.route("/delete-chat/<session_id>", methods=["DELETE"])
def delete_chat_route(session_id):
    if delete_chat(session_id):
        return jsonify({"success": True})
    return jsonify({"success": False}), 404


@chat_bp.route("/rename-chat/<session_id>", methods=["POST"])
def rename_chat_route(session_id):
    data      = request.json or {}
    new_title = data.get("title", "").strip()
    if not new_title:
        return jsonify({"success": False}), 400
    if rename_chat(session_id, new_title):
        return jsonify({"success": True})
    return jsonify({"success": False}), 404


@chat_bp.route("/chat", methods=["POST"])
def chat():
    start        = time.time()
    data         = request.json or {}
    user_message = data.get("message", "").strip()
    session_id   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # 1. Image generation
        if is_image_request(user_message):
            prompt = extract_image_prompt(user_message)
            result = generate_image(prompt)
            if result["success"]:
                add_to_memory(session_id, "user", user_message)
                add_to_memory(session_id, "assistant", f"Generated image: {prompt}")
                return jsonify({
                    "reply":     f"Here is your generated image of **{prompt}**!",
                    "image_url": result["image_url"],
                    "type":      "image"
                })
            return jsonify({
                "reply": f"Image Error: {result.get('error')}",
                "type": "text"
            })

        # 2. Code execution
        if is_code_request(user_message):
            code = extract_code(user_message)
            if code:
                safe, dangerous_item = is_safe_code(code)
                if safe:
                    result = execute_code(code)
                    reply  = (
                        f"**Code Output:**\n```\n{result['output']}\n```"
                        if result["success"]
                        else f"**Error:**\n```\n{result['error']}\n```"
                    )
                else:
                    reply = f"⚠️ Unsafe operation detected: `{dangerous_item}`. This code cannot be executed."
                add_to_memory(session_id, "user", user_message)
                add_to_memory(session_id, "assistant", reply)
                return jsonify({"reply": reply, "type": "code"})

        # 3. Web search
        print(f"🔍 Checking if search needed for: {user_message}")
        if needs_web_search(user_message):
            print(f"🔍 Search TRIGGERED for: {user_message}")

            search_query = _resolve_pronoun(user_message, session_id)
            memory = get_memory(session_id)
            conversation_context = build_conversation_context(memory)

            try:
                web_context = combined_search(search_query)
                print(f"📄 Search returned {len(web_context)} chars")
                print(f"🔍 SEARCH PREVIEW: {web_context[:400]}")

                if web_context and web_context != "No results found." and len(web_context) > 50 and _context_is_relevant(web_context, user_message):

                    # ✅ Low-confidence check: don't let AI guess wrong person
                    if _is_low_confidence_result(web_context, user_message):
                        reply = (
                            "I couldn't find reliable information about this person. "
                            "They may not be widely documented online. "
                            "Could you give more context, like their profession or location?"
                        )
                        add_to_memory(session_id, "user", user_message)
                        add_to_memory(session_id, "assistant", reply)
                        return jsonify({"reply": reply, "type": "text"})

                    messages = build_search_prompt(user_message, web_context, conversation_context)
                    reply = ask_mistral(messages)
                    print("\n================ REPLY ================\n")
                    print(reply)
                    print("\n==========================================\n")
                    add_to_memory(session_id, "user", user_message)
                    add_to_memory(session_id, "assistant", reply)
                    return jsonify({"reply": reply, "type": "search"})

                else:
                    print("⚠️ Search returned no useful results.")
                    reply = "I searched for this but could not find any reliable information."
                    add_to_memory(session_id, "user", user_message)
                    add_to_memory(session_id, "assistant", reply)
                    return jsonify({"reply": reply, "type": "text"})

            except Exception as e:
                print(f"❌ Search failed: {e}")
                reply = "I tried to search for this information but encountered an error."
                add_to_memory(session_id, "user", user_message)
                add_to_memory(session_id, "assistant", reply)
                return jsonify({"reply": reply, "type": "text"})

        # 4. Normal chat
        print(f"🔍 Search NOT triggered for: {user_message}")
        print(f"⏱ Before model call: {time.time() - start:.2f}s")
        messages = build_messages_with_memory(SYSTEM_PROMPT, user_message, session_id)
        reply = ask_mistral(messages)
        print(f"⏱ After model reply: {time.time() - start:.2f}s")

        add_to_memory(session_id, "user", user_message)
        add_to_memory(session_id, "assistant", reply)
        print(f"⏱ TOTAL: {time.time() - start:.2f}s")
        return jsonify({"reply": reply, "type": "text"})

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({"reply": f"Something went wrong: {str(e)}"}), 500


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data         = request.json or {}
    user_message = data.get("message", "")
    session_id   = data.get("session_id", "default")

    search_query = _resolve_pronoun(user_message, session_id)
    
    search_context = None
    if needs_web_search(search_query):
        try:
            search_context = combined_search(search_query)
            print(f"📄 Stream search returned {len(search_context) if search_context else 0} chars")
        except Exception as e:
            print(f"❌ Search failed in stream: {e}")

    if search_context and search_context != "No results found." and len(search_context) > 50:
        memory = get_memory(session_id)
        conversation_context = build_conversation_context(memory)
        messages = build_search_prompt(user_message, search_context, conversation_context)
    else:
        messages = build_messages_with_memory(SYSTEM_PROMPT, user_message, session_id)

    def generate():
        full_reply = ""
        for chunk in ask_mistral_stream(messages):
            full_reply += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        add_to_memory(session_id, "user", user_message)
        add_to_memory(session_id, "assistant", full_reply)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@chat_bp.route("/clear-memory", methods=["POST"])
def clear_memory_route():
    from services.memory import clear_memory
    data       = request.json or {}
    session_id = data.get("session_id", "default")
    clear_memory(session_id)
    return jsonify({"status": "Memory cleared!"})