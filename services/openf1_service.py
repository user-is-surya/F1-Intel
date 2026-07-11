"""
F1Intel — OpenF1 API Service
All errors are silent — returns empty list/None on any failure.
"""

from __future__ import annotations
import streamlit as st
import logging
from config.settings import OPENF1_BASE, CURRENT_SEASON, HTTP_TIMEOUT
from services.http_client import get_json

log = logging.getLogger(__name__)


def _get(endpoint: str, params: dict | None = None, timeout: int = HTTP_TIMEOUT) -> list | dict | None:
    url = f"{OPENF1_BASE}/{endpoint}"
    return get_json(url, params=params, timeout=timeout)


@st.cache_data(ttl=3600, show_spinner=False)
def get_sessions(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get("sessions", {"year": season})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_latest_session() -> dict | None:
    data = _get("sessions", {"session_key": "latest"})
    return data[0] if isinstance(data, list) and data else None


@st.cache_data(ttl=30, show_spinner=False)
def get_live_session() -> dict | None:
    """Returns current live session if one exists right now."""
    sessions = _get("sessions", {"year": CURRENT_SEASON})
    if not isinstance(sessions, list):
        return None
    from datetime import datetime, timedelta
    import pytz
    now = datetime.now(pytz.UTC)
    for s in reversed(sessions):
        try:
            start = datetime.fromisoformat(s.get("date_start", "").replace("Z", "+00:00"))
            end_str = s.get("date_end", "")
            if end_str:
                end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            else:
                # OpenF1 leaves date_end empty/null while a session is STILL
                # LIVE (this was the actual bug — sessions in progress were
                # being skipped entirely). Fall back to start + a generous
                # max session duration so an in-progress session is still
                # detected as live.
                end = start + timedelta(hours=3)
            if start <= now <= end:
                return s
        except Exception:
            continue
    return None


@st.cache_data(ttl=300, show_spinner=False)
def get_drivers_for_session(session_key: int | str) -> list[dict]:
    data = _get("drivers", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=8, show_spinner=False)
def get_live_positions(session_key: int | str) -> list[dict]:
    data = _get("position", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=8, show_spinner=False)
def get_live_intervals(session_key: int | str) -> list[dict]:
    data = _get("intervals", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=8, show_spinner=False)
def get_live_lap_times(session_key: int | str) -> list[dict]:
    data = _get("laps", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def get_car_data(session_key: int | str, driver_number: int) -> list[dict]:
    data = _get("car_data", {"session_key": session_key, "driver_number": driver_number})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def get_location_data(session_key: int | str, driver_number: int) -> list[dict]:
    data = _get("location", {"session_key": session_key, "driver_number": driver_number})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_pit_stops(session_key: int | str) -> list[dict]:
    data = _get("pit", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_stints(session_key: int | str) -> list[dict]:
    data = _get("stints", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=10, show_spinner=False)
def get_race_control(session_key: int | str) -> list[dict]:
    data = _get("race_control", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_weather(session_key: int | str) -> list[dict]:
    data = _get("weather", {"session_key": session_key})
    return data if isinstance(data, list) else []


def get_latest_weather(session_key: int | str) -> dict | None:
    records = get_weather(session_key)
    return records[-1] if records else None


@st.cache_data(ttl=300, show_spinner=False)
def get_team_radio(session_key: int | str) -> list[dict]:
    data = _get("team_radio", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def get_meetings(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get("meetings", {"year": season})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def get_latest_meeting() -> dict | None:
    data = _get("meetings", {"meeting_key": "latest"})
    return data[0] if isinstance(data, list) and data else None


@st.cache_data(ttl=5, show_spinner=False)
def get_all_location_data(session_key: int | str) -> list[dict]:
    """Get location data for ALL drivers in a session (no driver filter)."""
    data = _get("location", {"session_key": session_key})
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60, show_spinner=False)
def get_driver_location_history(session_key: int | str, driver_number: int) -> list[dict]:
    """Get full location history for one driver (used to draw circuit outline)."""
    data = _get("location", {"session_key": session_key, "driver_number": driver_number})
    return data if isinstance(data, list) else []
