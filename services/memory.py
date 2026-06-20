# memory.py — Conversation Memory Manager

chat_sessions = {}
def get_chat_history(session_id):
    return chat_sessions.get(session_id, [])
def get_memory(session_id="default"):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]
def delete_chat(session_id):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return True
    return False
def rename_chat(session_id, new_title):
    if session_id in chat_sessions:
        for msg in chat_sessions[session_id]:
            if msg["role"] == "user":
                msg["content"] = new_title
                return True
    return False

def add_to_memory(session_id, role, content):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    chat_sessions[session_id].append({
        "role": role,
        "content": content
    })
    # Keep only last 20 messages to save memory
    if len(chat_sessions[session_id]) > 20:
        chat_sessions[session_id] = chat_sessions[session_id][-20:]

def clear_memory(session_id="default"):
    chat_sessions[session_id] = []

def get_all_chats():
    chats = []
    for session_id, messages in chat_sessions.items():
        title = "New Chat"
        for msg in messages:
            if msg["role"] == "user":
                title = msg["content"][:40]
                break
        chats.append({
            "id": session_id,
            "title": title
        })
    return chats

def get_user_name(session_id="default"):
    messages = get_memory(session_id)
    for msg in messages:
        if msg["role"] == "user":
            content = msg["content"].lower()
            if "my name is" in content:
                name = content.split("my name is")[-1].strip().split()[0]
                return name.capitalize()
            if "i am" in content:
                name = content.split("i am")[-1].strip().split()[0]
                return name.capitalize()
    return None

def build_messages_with_memory(system_prompt, user_message, session_id="default"):
    messages = [{"role": "system", "content": system_prompt}]
    history = get_memory(session_id)
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages