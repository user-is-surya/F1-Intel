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

SEARCH GROUNDING: Gemini's knowledge is frozen at its training cutoff
(currently ~January 2025 for every current model, 2.5 through 3.5 — see
https://ai.google.dev/gemini-api/docs/gemini-3). Pass use_search=True to
let the model run real Google searches during generation instead of
answering from memory alone. Off by default: the race-story generator
already gets fresh facts via the prompt context, so it doesn't need it
and enabling it there would just add latency/cost for no benefit. The
open-ended F1 chat is the feature that actually needs this.
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


def _search_tool():
    """Build the Google Search grounding tool. Imported lazily so this
    module still loads fine even if the installed google-genai version
    doesn't expose GoogleSearch for some reason."""
    from google.genai import types
    return types.Tool(google_search=types.GoogleSearch())


def _extract_search_queries(response) -> list[str]:
    """Pull out which search queries (if any) the model actually ran,
    so callers can show 'searched for: ...' instead of a silent guess
    about whether grounding did anything."""
    try:
        candidate = response.candidates[0]
        metadata = getattr(candidate, "grounding_metadata", None)
        if metadata and getattr(metadata, "web_search_queries", None):
            return list(metadata.web_search_queries)
    except Exception:
        pass
    return []


def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 4096,
    use_search: bool = False,
) -> dict:
    """
    Generate text from Gemini. Returns:
      {"ok": True, "text": "...", "search_queries": [...]} on success
      {"ok": False, "error": "user-friendly message", "detail": "raw exception str"} on failure
    Never raises — always check result["ok"] before using result["text"].

    use_search: if True, lets Gemini run real Google searches while
    answering (fixes "outdated answers" for anything after its training
    cutoff). Adds latency and a small per-grounded-prompt cost — see
    https://ai.google.dev/gemini-api/docs/pricing.
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
        if use_search:
            config.tools = [_search_tool()]

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
        return {"ok": True, "text": text, "search_queries": _extract_search_queries(response)}

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
    use_search: bool = False,
) -> dict:
    """
    Multi-turn chat. messages = [{"role": "user"|"model", "text": "..."}]
    Returns the same {"ok", "text"/"error", "search_queries"} shape as generate_text.

    use_search: if True, lets Gemini run real Google searches while
    replying — this is what the F1 Knowledge Chat should pass, since it's
    the feature people actually notice giving outdated answers.
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
        if use_search:
            config.tools = [_search_tool()]

        response = client.models.generate_content(
            model=get_model_name(),
            contents=contents,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text:
            return {"ok": False, "error": "Gemini returned an empty response.", "detail": "empty_response"}
        return {"ok": True, "text": text, "search_queries": _extract_search_queries(response)}

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
