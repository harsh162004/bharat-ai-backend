# ============================================================
# model.py — Smart AI Engine Router for Bharat.ai v4.0
# Priority: Groq first → OpenRouter Llama fallback
# Gemini only for Assamese language
# ============================================================

import requests
import warnings
warnings.filterwarnings("ignore")

from config import ENGINE_A_KEY, ENGINE_C_KEY, ENGINE_D_KEY, OLLAMA_URL, OLLAMA_MODEL

_ea = ENGINE_A_KEY   # Groq
_ec = ENGINE_C_KEY   # OpenRouter key  # OpenRouter key
_ee = ENGINE_D_KEY   # GLM
_ou = OLLAMA_URL
_om = OLLAMA_MODEL

_gok       = False
_ook       = False

_ga        = None

# ── Groq Model Cascade (priority order) ──────────────────────
GROQ_MODELS = [
    "openai/gpt-oss-120b",                            # strongest, try first
    "openai/gpt-oss-20b",                             # strong, lighter
    "llama-3.3-70b-versatile",                        # middle ground
    "meta-llama/llama-4-scout-17b-16e-instruct",      # solid fallback
    "llama-3.1-8b-instant",                            # no rate limit, last resort
]

# ── Init Groq (PRIMARY) ───────────────────────────────────────
try:
    from groq import Groq
    import groq as _groq_module  # for RateLimitError access
    _ga = Groq(api_key=_ea)
    _gok = True
    print("✅ Groq connected!")
except Exception as e:
    print(f"❌ Groq failed: {e}")

# ── Init OpenRouter (FALLBACK) ────────────────────────────────
try:
    import openai as _oa
    _ook = True
    print("✅ OpenRouter connected!")
except Exception as e:
    print(f"❌ OpenRouter failed: {e}")



# ── Engine: Groq ──────────────────────────────────────────────

def _groq(messages):
    if not _gok or _ga is None:
        raise RuntimeError("Groq unavailable")

    print("🚀 USING GROQ")

    for model_name in GROQ_MODELS:
        try:
            r = _ga.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            print(f"✅ Replied by Groq using: {model_name}")
            return r.choices[0].message.content
        except _groq_module.RateLimitError:
            print(f"⚠️ {model_name} rate-limited, trying next model...")
            continue
        # Other exceptions bubble up to ask_mistral's except block

    raise RuntimeError("All Groq models rate-limited")

# ── Engine: OpenRouter Llama (best free fallback) ─────────────

def _openrouter_llama(messages):
    if not _ook:
        raise RuntimeError("OpenRouter unavailable")
    import openai
    c = openai.OpenAI(
        api_key=_ec,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "http://localhost:5000", "X-Title": "Bharat.ai"},
        timeout=20
    )
    r = c.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=messages, max_tokens=800
    )
    return r.choices[0].message.content


# ── Engine: OpenRouter Mistral (second fallback) ──────────────

def _openrouter_mistral(messages):
    if not _ook:
        raise RuntimeError("OpenRouter unavailable")
    import openai
    c = openai.OpenAI(
        api_key=_ec,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "http://localhost:5000", "X-Title": "Bharat.ai"},
        timeout=20
    )
    r = c.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=messages, max_tokens=800
    )
    return r.choices[0].message.content


# ── Engine: Gemini (Assamese only) ────────────────────────────







# ── Main Entry Point ──────────────────────────────────────────

def ask_mistral(messages: list, stream: bool = False) -> str:
    # Stage 1: Groq — fastest, highest priority
    if _gok:
        try:
            reply = _groq(messages)
            if reply and reply.strip():
                print("✅ Replied by: Groq")
                return reply
        except Exception as e:
            print(f"❌ Groq failed: {e}")

    # Stage 2: OpenRouter Llama — best free fallback
    if _ook:
        try:
            reply = _openrouter_llama(messages)
            if reply and reply.strip():
                print("✅ Replied by: OpenRouter Llama")
                return reply
        except Exception as e:
            print(f"❌ OpenRouter Llama failed: {e}")

        # Stage 3: OpenRouter Mistral — second fallback
        try:
            reply = _openrouter_mistral(messages)
            if reply and reply.strip():
                print("✅ Replied by: OpenRouter Mistral")
                return reply
        except Exception as e:
            print(f"❌ OpenRouter Mistral failed: {e}")

    return "⚠️ Bharat.ai is temporarily unavailable. Please check your internet and try again."


# ── Streaming ─────────────────────────────────────────────────

def ask_mistral_stream(messages: list):
    """Stream from Groq if available, else simulate streaming."""
    if _gok and _ga is not None:
        for model_name in GROQ_MODELS:
            try:
                stream = _ga.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=800,
                    temperature=0.7,
                    stream=True
                )
                print(f"🚀 Streaming via Groq: {model_name}")
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return  # Stream completed successfully
            except _groq_module.RateLimitError:
                print(f"⚠️ {model_name} rate-limited, trying next model...")
                continue
            except Exception as e:
                print(f"⚠️ Groq stream failed on {model_name}: {e}")
                break  # Non-rate-limit error — fall through to simulation

    # Simulate streaming from normal reply
    try:
        full = ask_mistral(messages)
        for i in range(0, len(full), 30):
            yield full[i:i + 30]
    except Exception as e:
        yield f"Error: {str(e)}"