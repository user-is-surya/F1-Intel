"""
F1Intel — FastF1 Service
Silent errors throughout — returns None/empty on any failure.
"""

from __future__ import annotations
import fastf1
import pandas as pd
import streamlit as st
import logging
from typing import Optional
from config.settings import FASTF1_CACHE_DIR, CURRENT_SEASON

log = logging.getLogger(__name__)
fastf1.Cache.enable_cache(FASTF1_CACHE_DIR)
fastf1.set_log_level("DEBUG")  # TEMPORARY — need the actual underlying
# network exception (timeout vs 403 vs connection refused), not just
# FastF1's summarized "Failed to load X!" warnings. Turn this back down
# to "WARNING" once we've confirmed what's actually happening — DEBUG is
# very noisy and will bloat the logs if left on.


@st.cache_resource(show_spinner=False)
def load_session(season: int, gp: int, session: str) -> Optional[fastf1.core.Session]:
    for attempt in range(2):
        try:
            s = fastf1.get_session(season, gp, session)
            s.load(telemetry=True, weather=True, messages=True, laps=True)
            # On a freshly-woken (cold) container, the network call for the
            # detailed lap-by-lap timing data can be flaky and FastF1 hands
            # back an empty result WITHOUT raising — so "no exception" isn't
            # proof it actually worked. Catch that case and retry once.
            if (s.laps is None or s.laps.empty) and attempt == 0:
                log.warning("FastF1 load_session(%s, %s, %s): laps came back empty, retrying once", season, gp, session)
                print(f"[FastF1] load_session({season}, {gp}, {session}): laps empty, retrying")
                continue
            return s
        except Exception as e:
            # This used to be log.debug(), which is essentially invisible —
            # Streamlit Cloud's log viewer doesn't show DEBUG-level messages
            # by default, so a failure here looked like "no error at all"
            # even though something real was going wrong. log.error() (and
            # the print() as a belt-and-suspenders, since Cloud's log viewer
            # captures stdout too) makes the actual reason show up.
            log.error("FastF1 load_session(%s, %s, %s) failed: %s", season, gp, session, e)
            print(f"[FastF1] load_session({season}, {gp}, {session}) failed: {e!r}")
            if attempt == 0:
                continue
            return None
    return None


@st.cache_resource(show_spinner=False)
def load_session_basic(season: int, gp: int, session: str) -> Optional[fastf1.core.Session]:
    for attempt in range(2):
        try:
            s = fastf1.get_session(season, gp, session)
            s.load(telemetry=False, weather=True, messages=True, laps=True)
            if (s.laps is None or s.laps.empty) and attempt == 0:
                log.warning("FastF1 load_session_basic(%s, %s, %s): laps came back empty, retrying once", season, gp, session)
                print(f"[FastF1] load_session_basic({season}, {gp}, {session}): laps empty, retrying")
                continue
            return s
        except Exception as e:
            log.error("FastF1 load_session_basic(%s, %s, %s) failed: %s", season, gp, session, e)
            print(f"[FastF1] load_session_basic({season}, {gp}, {session}) failed: {e!r}")
            if attempt == 0:
                continue
            return None
    return None


def get_laps(session: fastf1.core.Session) -> pd.DataFrame:
    try:
        return session.laps
    except Exception:
        return pd.DataFrame()


def get_driver_laps(session: fastf1.core.Session, driver_abbr: str) -> pd.DataFrame:
    try:
        return session.laps.pick_drivers(driver_abbr)
    except Exception:
        return pd.DataFrame()


def get_fastest_lap(session: fastf1.core.Session, driver_abbr: str):
    try:
        return session.laps.pick_drivers(driver_abbr).pick_fastest()
    except Exception:
        return None


def get_lap_telemetry(lap, channels: list[str] | None = None) -> pd.DataFrame:
    try:
        tel = lap.get_car_data().add_distance()
        if channels:
            cols = [c for c in channels if c in tel.columns] + ["Distance"]
            tel = tel[cols]
        return tel
    except Exception:
        return pd.DataFrame()


def get_pos_data(lap) -> pd.DataFrame:
    try:
        return lap.get_pos_data()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_event_schedule(season: int = CURRENT_SEASON) -> pd.DataFrame:
    try:
        return fastf1.get_event_schedule(season, include_testing=False)
    except Exception:
        return pd.DataFrame()


def get_next_event(season: int = CURRENT_SEASON):
    try:
        schedule = get_event_schedule(season)
        if schedule.empty:
            return None
        from datetime import datetime
        import pytz
        now = datetime.now(pytz.UTC)
        future = schedule[schedule["EventDate"] > pd.Timestamp(now)]
        return future.iloc[0] if not future.empty else None
    except Exception:
        return None


def get_last_event(season: int = CURRENT_SEASON):
    try:
        schedule = get_event_schedule(season)
        if schedule.empty:
            return None
        from datetime import datetime
        import pytz
        now = datetime.now(pytz.UTC)
        past = schedule[schedule["EventDate"] <= pd.Timestamp(now)]
        return past.iloc[-1] if not past.empty else None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False, persist="disk")
def get_circuit_info(season: int, gp: int) -> dict:
    try:
        event = fastf1.get_event(season, gp)
        return {
            "name":     event.get("EventName", ""),
            "location": event.get("Location", ""),
            "country":  event.get("Country", ""),
            "date":     str(event.get("EventDate", "")),
            "round":    event.get("RoundNumber", 0),
            "format":   event.get("EventFormat", "conventional"),
        }
    except Exception:
        return {}


def get_session_drivers(session: fastf1.core.Session) -> list[str]:
    """
    Return driver three-letter abbreviations (e.g. 'VER', 'HAM') for this
    session — NOT raw driver numbers. session.drivers gives numbers
    ('1', '44', ...), but session.laps['Driver'] (used everywhere else
    in this app: tire stints, lap evolution, degradation, telemetry) is
    keyed by abbreviation. Resolving here once means every page that
    calls this function gets consistent, matching driver identifiers.
    """
    try:
        abbrs = []
        for num in session.drivers:
            try:
                abbr = session.get_driver(num).get("Abbreviation", "")
                if abbr:
                    abbrs.append(abbr)
            except Exception:
                continue
        return abbrs
    except Exception:
        return []


def get_driver_info_ff1(session: fastf1.core.Session, driver_abbr: str) -> dict:
    try:
        info = session.get_driver(driver_abbr)
        return {
            "abbreviation": driver_abbr,
            "full_name":    info.get("FullName", driver_abbr),
            "number":       str(info.get("DriverNumber", "")),
            "team":         info.get("TeamName", ""),
            "team_color":   f"#{info.get('TeamColor', 'E10600')}",
        }
    except Exception:
        return {"abbreviation": driver_abbr, "full_name": driver_abbr,
                "number": "", "team": "", "team_color": "#E10600"}


def get_sector_times(session: fastf1.core.Session) -> pd.DataFrame:
    try:
        cols = ["Driver", "LapNumber", "Sector1Time", "Sector2Time",
                "Sector3Time", "LapTime", "Compound", "TyreLife"]
        available = [c for c in cols if c in session.laps.columns]
        return session.laps[available].dropna(subset=["LapTime"])
    except Exception:
        return pd.DataFrame()


def get_tire_stints(session: fastf1.core.Session) -> pd.DataFrame:
    try:
        cols = ["Driver", "Stint", "Compound", "TyreLife", "LapNumber", "LapTime"]
        available = [c for c in cols if c in session.laps.columns]
        laps = session.laps[available].copy()
        laps = laps.dropna(subset=["Compound"])
        stints = (
            laps.groupby(["Driver", "Stint", "Compound"], group_keys=False)
            .agg(
                first_lap=("LapNumber", "min"),
                last_lap=("LapNumber", "max"),
                laps=("LapNumber", "count"),
                avg_lap=("LapTime", lambda x: x.dt.total_seconds().mean()
                          if hasattr(x.iloc[0] if len(x) > 0 else 0, "total_seconds") else 0),
            )
            .reset_index()
        )
        return stints
    except Exception:
        return pd.DataFrame()
