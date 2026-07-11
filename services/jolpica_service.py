"""
F1Intel — Jolpica API Service
Wraps the Jolpica (Ergast-compatible) REST API.
Base: https://api.jolpi.ca/ergast/f1
All errors are silent — returns empty list/None instead of crashing.
"""

from __future__ import annotations
import streamlit as st
import logging
from config.settings import JOLPICA_BASE, CURRENT_SEASON, HTTP_TIMEOUT
from services.http_client import get_json

log = logging.getLogger(__name__)


def _get(path: str, params: dict | None = None, timeout: int = HTTP_TIMEOUT) -> dict | None:
    url = f"{JOLPICA_BASE}/{path}.json"
    data = get_json(url, params=params, timeout=timeout)
    if data is None:
        log.debug("Jolpica request failed or returned no data: %s", url)
    return data


# ── Driver Standings ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_driver_standings(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/driverStandings")
    if not data:
        return []
    try:
        sl = data["MRData"]["StandingsTable"]["StandingsLists"]
        return sl[0]["DriverStandings"] if sl else []
    except (KeyError, IndexError):
        return []


# ── Constructor Standings ────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_constructor_standings(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/constructorStandings")
    if not data:
        return []
    try:
        sl = data["MRData"]["StandingsTable"]["StandingsLists"]
        return sl[0]["ConstructorStandings"] if sl else []
    except (KeyError, IndexError):
        return []


# ── Race Schedule ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_schedule(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}")
    if not data:
        return []
    try:
        return data["MRData"]["RaceTable"]["Races"]
    except KeyError:
        return []


# ── Race Results ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_race_results(season: int, round_num: int | str) -> list[dict]:
    data = _get(f"{season}/{round_num}/results")
    if not data:
        return []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        return races[0].get("Results", []) if races else []
    except (KeyError, IndexError):
        return []


@st.cache_data(ttl=600, show_spinner=False)
def get_last_race_results(season: int = CURRENT_SEASON) -> tuple[dict | None, list[dict]]:
    data = _get(f"{season}/last/results")
    if not data:
        return None, []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return None, []
        race = races[0]
        return race, race.get("Results", [])
    except (KeyError, IndexError):
        return None, []


# ── Qualifying Results ───────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_qualifying_results(season: int, round_num: int | str) -> list[dict]:
    data = _get(f"{season}/{round_num}/qualifying")
    if not data:
        return []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        return races[0].get("QualifyingResults", []) if races else []
    except (KeyError, IndexError):
        return []


# ── Sprint Results ───────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_sprint_results(season: int, round_num: int | str) -> list[dict]:
    data = _get(f"{season}/{round_num}/sprint")
    if not data:
        return []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        return races[0].get("SprintResults", []) if races else []
    except (KeyError, IndexError):
        return []


# ── Pit Stops ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_pit_stops(season: int, round_num: int | str) -> list[dict]:
    data = _get(f"{season}/{round_num}/pitstops", {"limit": 200})
    if not data:
        return []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        return races[0].get("PitStops", []) if races else []
    except (KeyError, IndexError):
        return []


# ── Driver Info ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_drivers(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/drivers")
    if not data:
        return []
    try:
        return data["MRData"]["DriverTable"]["Drivers"]
    except KeyError:
        return []


@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_driver_info(driver_id: str) -> dict | None:
    data = _get(f"drivers/{driver_id}")
    if not data:
        return None
    try:
        drivers = data["MRData"]["DriverTable"]["Drivers"]
        return drivers[0] if drivers else None
    except (KeyError, IndexError):
        return None


@st.cache_data(ttl=600, show_spinner=False)
def get_driver_season_results(driver_id: str, season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/drivers/{driver_id}/results", {"limit": 50})
    if not data:
        return []
    try:
        return data["MRData"]["RaceTable"]["Races"]
    except KeyError:
        return []


@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_driver_career_stats(driver_id: str) -> dict:
    wins  = _count_total(f"drivers/{driver_id}/results/1")
    poles = _count_total(f"drivers/{driver_id}/qualifying/1")
    return {"wins": wins, "poles": poles}


def _count_total(path: str) -> int:
    data = _get(path, {"limit": 1})
    if not data:
        return 0
    try:
        return int(data["MRData"].get("total", 0))
    except Exception:
        return 0


# ── Constructors ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_constructors(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/constructors")
    if not data:
        return []
    try:
        return data["MRData"]["ConstructorTable"]["Constructors"]
    except KeyError:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def get_constructor_season_results(constructor_id: str, season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/constructors/{constructor_id}/results", {"limit": 100})
    if not data:
        return []
    try:
        return data["MRData"]["RaceTable"]["Races"]
    except KeyError:
        return []


# ── Circuits ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_circuits(season: int = CURRENT_SEASON) -> list[dict]:
    data = _get(f"{season}/circuits")
    if not data:
        return []
    try:
        return data["MRData"]["CircuitTable"]["Circuits"]
    except KeyError:
        return []


@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_circuit_history(circuit_id: str, limit: int = 30) -> list[dict]:
    data = _get(f"circuits/{circuit_id}/results/1", {"limit": limit})
    if not data:
        return []
    try:
        return data["MRData"]["RaceTable"]["Races"]
    except KeyError:
        return []


# ── Season list ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_all_seasons() -> list[str]:
    data = _get("seasons", {"limit": 100, "offset": 0})
    if not data:
        return [str(y) for y in range(CURRENT_SEASON, 1949, -1)]
    try:
        seasons = data["MRData"]["SeasonTable"]["Seasons"]
        return [s["season"] for s in reversed(seasons)]
    except KeyError:
        return [str(y) for y in range(CURRENT_SEASON, 1949, -1)]


@st.cache_data(ttl=3600, show_spinner=False)
def get_season_champion(season: int) -> dict | None:
    standings = get_driver_standings(season)
    return standings[0] if standings else None


@st.cache_data(ttl=3600, show_spinner=False)
def get_fastest_laps(season: int, round_num: int | str) -> list[dict]:
    data = _get(f"{season}/{round_num}/fastest/1/results")
    if not data:
        return []
    try:
        races = data["MRData"]["RaceTable"]["Races"]
        return races[0].get("Results", []) if races else []
    except (KeyError, IndexError):
        return []


@st.cache_data(ttl=120, show_spinner=False)
def get_latest_standings(season: int = CURRENT_SEASON) -> list[dict]:
    """
    Get the most current driver standings.
    Tries /current/driverStandings first (always latest), then falls back to season.
    """
    # Try 'current' endpoint first — always the most recent standings
    data = _get("current/driverStandings")
    if data:
        try:
            sl = data["MRData"]["StandingsTable"]["StandingsLists"]
            if sl:
                return sl[0]["DriverStandings"]
        except (KeyError, IndexError):
            pass
    # Fall back to season-specific
    return get_driver_standings(season)


@st.cache_data(ttl=120, show_spinner=False)
def get_latest_constructor_standings(season: int = CURRENT_SEASON) -> list[dict]:
    """Always-current constructor standings."""
    data = _get("current/constructorStandings")
    if data:
        try:
            sl = data["MRData"]["StandingsTable"]["StandingsLists"]
            if sl:
                return sl[0]["ConstructorStandings"]
        except (KeyError, IndexError):
            pass
    return get_constructor_standings(season)
