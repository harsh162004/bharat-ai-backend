# ============================================================
# executor.py — Advanced Safe Code Executor for Bharat.ai
# Supports: Python (sandbox) | JavaScript | HTML preview
# Features: Auto-detect, Execution time, Line numbers, Safe sandbox
# BCA 6th Semester | Dibrugarh University
# Built by Harsh Raut & Shanu Das
# ============================================================

import sys
import io
import traceback
import re
import time


# ============================================================
# PYTHON EXECUTOR — Safe Sandbox
# ============================================================
def execute_code(code):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout  = io.StringIO()
    sys.stderr  = io.StringIO()

    start_time = time.time()

    try:
        exec_globals = {
            "__builtins__": {
                # Output
                "print": print,
                # Types
                "int": int, "float": float, "str": str,
                "bool": bool, "list": list, "dict": dict,
                "tuple": tuple, "set": set, "bytes": bytes,
                # Math
                "abs": abs, "max": max, "min": min,
                "sum": sum, "round": round, "pow": pow,
                "divmod": divmod,
                # Iterators
                "range": range, "len": len, "sorted": sorted,
                "reversed": reversed, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "any": any, "all": all,
                # Type checking
                "type": type, "isinstance": isinstance,
                "issubclass": issubclass, "callable": callable,
                "hasattr": hasattr, "getattr": getattr,
                # String / repr
                "repr": repr, "chr": chr, "ord": ord,
                "hex": hex, "oct": oct, "bin": bin,
                # Functional
                "vars": vars, "dir": dir,
                # Safe input (returns empty string)
                "input": lambda x="": "",
                # Math module allowed
                "__import__": _safe_import,
            }
        }

        exec(code, exec_globals)

        output = sys.stdout.getvalue()
        error  = sys.stderr.getvalue()
        elapsed = round((time.time() - start_time) * 1000, 2)

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        if error:
            return {
                "success":  False,
                "output":   "",
                "error":    _format_error(error),
                "language": "python",
                "time_ms":  elapsed
            }

        return {
            "success":  True,
            "output":   output if output else "✅ Code executed successfully (no output)",
            "error":    "",
            "language": "python",
            "time_ms":  elapsed
        }

    except Exception:
        elapsed = round((time.time() - start_time) * 1000, 2)
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return {
            "success":  False,
            "output":   "",
            "error":    _format_error(traceback.format_exc()),
            "language": "python",
            "time_ms":  elapsed
        }


# ============================================================
# SAFE IMPORT — only allows math, random, datetime, string
# ============================================================
def _safe_import(name, *args, **kwargs):
    allowed = ["math", "random", "datetime", "string", "json",
               "collections", "itertools", "functools", "re"]
    if name in allowed:
        return __import__(name, *args, **kwargs)
    raise ImportError(f"❌ Import '{name}' is not allowed in Bharat.ai sandbox.")


# ============================================================
# ERROR FORMATTER — adds line numbers to errors
# ============================================================
def _format_error(error_text):
    lines = error_text.strip().split("\n")
    formatted = []
    for line in lines:
        # Highlight line number references
        line = re.sub(r'line (\d+)', r'📍 Line \1', line)
        formatted.append(line)
    return "\n".join(formatted)


# ============================================================
# JAVASCRIPT DETECTOR & EXTRACTOR
# ============================================================
def is_javascript(code):
    js_signals = [
        "console.log", "let ", "const ", "var ",
        "function ", "=>", "document.", "window.",
        "addEventListener", "querySelector", "innerHTML",
        "setTimeout", "setInterval", "Promise", "async ",
        "await ", "fetch(", "JSON.parse", "JSON.stringify"
    ]
    return any(sig in code for sig in js_signals)


def handle_javascript(code):
    """Returns info that JS should be run in browser."""
    return {
        "success":  True,
        "output":   "🌐 JavaScript detected! This code runs in the browser.\n\nOpen browser console (F12) and paste the code there to run it.",
        "error":    "",
        "language": "javascript",
        "time_ms":  0
    }


# ============================================================
# HTML DETECTOR
# ============================================================
def is_html(code):
    html_signals = [
        "<!DOCTYPE", "<html", "<body", "<div",
        "<p>", "<h1", "<h2", "<h3", "<form",
        "<input", "<button", "<style", "<script"
    ]
    code_upper = code.upper()
    return any(sig.upper() in code_upper for sig in html_signals)


def handle_html(code):
    """Returns info that HTML should be previewed in browser."""
    return {
        "success":  True,
        "output":   "🌐 HTML detected! Save this as a .html file and open in your browser to preview it.",
        "error":    "",
        "language": "html",
        "time_ms":  0
    }


# ============================================================
# CODE EXTRACTOR — detects code blocks in any message
# ============================================================
def extract_code(message):
    # Try to find ```python ... ``` or ```js ... ``` or ``` ... ```
    pattern = r"```(?:python|javascript|js|html|py)?\n?(.*?)```"
    matches = re.findall(pattern, message, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return None


def extract_language(message):
    """Detect language from code fence label."""
    pattern = r"```(python|javascript|js|html|py)"
    match = re.search(pattern, message, re.IGNORECASE)
    if match:
        lang = match.group(1).lower()
        if lang in ["js", "javascript"]:
            return "javascript"
        if lang == "html":
            return "html"
        return "python"
    return "python"


# ============================================================
# AUTO DETECT — no need to say "run this code" anymore
# ============================================================
def is_code_request(message):
    # Explicit keywords
    keywords = [
        "run this code", "execute this", "run this",
        "execute code", "run code", "check this code",
        "test this code", "run the code", "execute the code",
        "can you run", "please run", "run it",
    ]
    message_lower = message.lower()
    for keyword in keywords:
        if keyword in message_lower:
            return True

    # Auto detect — if message has a code block, treat as execution request
    if extract_code(message):
        return True

    return False


# ============================================================
# SAFETY CHECKER — fixed, no false positives
# ============================================================
def is_safe_code(code):
    dangerous = [
        "import os", "import sys", "import subprocess",
        "import shutil", "import socket", "import threading",
        "import multiprocessing", "open(", "exec(", "eval(",
        "__import__", "os.system", "os.remove", "os.rmdir",
        "os.path", "subprocess", "shutil.rmtree", "shutil.copy",
        "sys.exit", "sys.argv", "globals()", "locals()",
        "compile(", "breakpoint(",
    ]
    for d in dangerous:
        if d in code:
            return False, d
    return True, None

# ============================================================
# MAIN SMART RUNNER — handles Python, JS, HTML automatically
# ============================================================
def smart_execute(message):
    """
    Main entry point.
    Extracts code from message, detects language,
    runs safely and returns result dict.
    """
    code = extract_code(message)
    if not code:
        return {
            "success": False,
            "output": "",
            "error": "No code block found. Please wrap your code in ``` backticks.",
            "language": "unknown",
            "time_ms": 0
        }

    lang = extract_language(message)

    # Auto-detect language from code content if not specified
    if lang == "python" and is_javascript(code):
        lang = "javascript"
    elif lang == "python" and is_html(code):
        lang = "html"

    # Handle JS
    if lang == "javascript":
        return handle_javascript(code)

    # Handle HTML
    if lang == "html":
        return handle_html(code)

    # Python — safety check first
    safe, dangerous_item = is_safe_code(code)
    if not safe:
        return {
            "success": False,
            "output": "",
            "error": f"⚠️ Unsafe operation detected: `{dangerous_item}`\nThis operation is blocked for security reasons.",
            "language": "python",
            "time_ms": 0
        }

    # Execute Python safely
    return execute_code(code)