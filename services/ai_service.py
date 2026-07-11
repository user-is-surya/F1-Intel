"""
F1Intel — AI Service
Wraps Google Gemini (via the google-genai SDK) for two features:
  1. AI Race Story Generator — narrative race summaries
  2. Race Command Center — conversational Q&A about live/recent sessions
     and general Formula 1 knowledge

API key comes from .streamlit/secrets.toml under [gemini] api_key — see
.streamlit/secrets.toml.example for the template. Never hardcoded here.

All functions degrade gracefully when no key is configured: they return
a clear status dict rather than raising, so calling pages can show a
friendly "AI features need a Gemini API key" message instead of crashing.
"""

from __future__ import annotations
import streamlit as st
import logging

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash"


def get_api_key() -> str | None:
    """Read the Gemini API key from Streamlit secrets, if configured."""
    try:
        return st.secrets.get("gemini", {}).get("api_key")
    except Exception:
        return None


def is_configured() -> bool:
    """True if a usable-looking API key is present."""
    key = get_api_key()
    return bool(key) and key != "PASTE_YOUR_GEMINI_API_KEY_HERE"


def get_model_name() -> str:
    try:
        return st.secrets.get("gemini", {}).get("model", DEFAULT_MODEL)
    except Exception:
        return DEFAULT_MODEL


@st.cache_resource(show_spinner=False)
def _get_client():
    """Create (and cache) the Gemini client. Returns None if unconfigured."""
    if not is_configured():
        return None
    try:
        from google import genai
        return genai.Client(api_key=get_api_key())
    except Exception as e:
        log.debug("Failed to create Gemini client: %s", e)
        return None


def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 4096,
) -> dict:
    """
    Generate text from Gemini. Returns:
      {"ok": True, "text": "..."} on success
      {"ok": False, "error": "user-friendly message", "detail": "raw exception str"} on failure
    Never raises — always check result["ok"] before using result["text"].
    """
    if not is_configured():
        return {
            "ok": False,
            "error": "No Gemini API key configured. Add one to .streamlit/secrets.toml to enable AI features.",
            "detail": "missing_api_key",
        }

    client = _get_client()
    if client is None:
        return {
            "ok": False,
            "error": "Could not connect to Gemini. Check your API key is valid.",
            "detail": "client_init_failed",
        }

    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        response = client.models.generate_content(
            model=get_model_name(),
            contents=prompt,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text:
            return {
                "ok": False,
                "error": "Gemini returned an empty response. Try again in a moment.",
                "detail": "empty_response",
            }
        return {"ok": True, "text": text}

    except Exception as e:
        err_str = str(e)
        err_lower = err_str.lower()
        # Surface the most common, actionable failure modes with a clear message
        if "allowlist" in err_lower or "network" in err_lower and "egress" in err_lower:
            friendly = "Network blocked the request to Gemini (firewall/egress rules). Check your network settings."
        elif "429" in err_str or "quota" in err_lower or "rate" in err_lower:
            friendly = "Gemini's free-tier rate limit was hit. Wait a minute and try again."
        elif "401" in err_str or "403" in err_str or "api key" in err_lower or "permission" in err_lower:
            friendly = "Gemini rejected the API key. Double-check it in .streamlit/secrets.toml."
        elif "timeout" in err_lower:
            friendly = "Gemini took too long to respond. Try again."
        else:
            friendly = "Something went wrong talking to Gemini. Try again in a moment."
        log.debug("Gemini generation failed: %s", err_str)
        return {"ok": False, "error": friendly, "detail": err_str}


def generate_chat_reply(
    messages: list[dict],
    system_instruction: str | None = None,
    temperature: float = 0.4,
) -> dict:
    """
    Multi-turn chat. messages = [{"role": "user"|"model", "text": "..."}]
    Returns the same {"ok", "text"/"error"} shape as generate_text.
    """
    if not is_configured():
        return {
            "ok": False,
            "error": "No Gemini API key configured. Add one to .streamlit/secrets.toml to enable the chat.",
            "detail": "missing_api_key",
        }

    client = _get_client()
    if client is None:
        return {
            "ok": False,
            "error": "Could not connect to Gemini. Check your API key is valid.",
            "detail": "client_init_failed",
        }

    try:
        from google.genai import types

        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=m.get("text", ""))],
            ))

        config = types.GenerateContentConfig(temperature=temperature, max_output_tokens=2048)
        if system_instruction:
            config.system_instruction = system_instruction

        response = client.models.generate_content(
            model=get_model_name(),
            contents=contents,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text:
            return {"ok": False, "error": "Gemini returned an empty response.", "detail": "empty_response"}
        return {"ok": True, "text": text}

    except Exception as e:
        err_str = str(e)
        err_lower = err_str.lower()
        if "allowlist" in err_lower or ("network" in err_lower and "egress" in err_lower):
            friendly = "Network blocked the request to Gemini (firewall/egress rules). Check your network settings."
        elif "429" in err_str or "quota" in err_lower or "rate" in err_lower:
            friendly = "Gemini's free-tier rate limit was hit. Wait a minute and try again."
        elif "401" in err_str or "403" in err_str or "api key" in err_lower:
            friendly = "Gemini rejected the API key. Double-check it in .streamlit/secrets.toml."
        else:
            friendly = "Something went wrong talking to Gemini. Try again in a moment."
        log.debug("Gemini chat failed: %s", err_str)
        return {"ok": False, "error": friendly, "detail": err_str}
