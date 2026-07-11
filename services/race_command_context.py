"""
F1Intel — Race Command Center Context Builder
Converts raw live/recent session data (positions, intervals, lap times,
stints, pit stops, race control) into a compact, structured text summary
that the AI can answer questions about accurately.

DESIGN NOTE (honesty about what this can and can't do): the AI does not
"read telemetry" and discover insights on its own — it answers based on
the pre-computed summary built here. This means common questions (gaps,
tire age, who's fastest, pit stop counts, recent race control events) get
accurate, grounded answers because the relevant numbers are explicitly
in the context. Questions far outside what's summarized below may get
vaguer answers, since the AI is reasoning over a snapshot, not live raw
telemetry streams.
"""

from __future__ import annotations
from services.openf1_service import (
    get_drivers_for_session, get_live_positions, get_live_intervals,
    get_live_lap_times, get_stints, get_pit_stops, get_race_control,
    get_latest_weather,
)
from config.teams import get_team_color


def build_session_context(session_key, session_label: str = "") -> str:
    """
    Build a compact text summary of the current session state, covering
    positions, gaps, tire compounds/age, recent pit stops, fastest lap
    holder, and the most recent race control messages.
    """
    drivers_info  = get_drivers_for_session(session_key)
    positions_raw = get_live_positions(session_key)
    intervals_raw = get_live_intervals(session_key)
    lap_times_raw = get_live_lap_times(session_key)
    stints_raw    = get_stints(session_key)
    pit_stops_raw = get_pit_stops(session_key)
    rc_messages   = get_race_control(session_key)
    weather       = get_latest_weather(session_key)

    driver_map = {d.get("driver_number"): d for d in drivers_info}

    interval_map = {}
    for iv in intervals_raw:
        n = iv.get("driver_number")
        if n: interval_map[n] = iv

    lap_map = {}
    for lp in lap_times_raw:
        n = lp.get("driver_number")
        if n and lp.get("lap_number", 0) > lap_map.get(n, {}).get("lap_number", 0):
            lap_map[n] = lp

    stint_map = {}
    for s in stints_raw:
        n = s.get("driver_number")
        if n and s.get("stint_number", 0) >= stint_map.get(n, {}).get("stint_number", 0):
            stint_map[n] = s

    pit_count: dict[int, int] = {}
    last_pit: dict[int, dict] = {}
    for ps in pit_stops_raw:
        n = ps.get("driver_number")
        if n:
            pit_count[n] = pit_count.get(n, 0) + 1
            if ps.get("date", "") >= last_pit.get(n, {}).get("date", ""):
                last_pit[n] = ps

    latest_pos = {}
    for pe in positions_raw:
        n = pe.get("driver_number")
        if n and pe.get("date", "") >= latest_pos.get(n, {}).get("date", ""):
            latest_pos[n] = pe

    sorted_drivers = sorted(latest_pos.items(), key=lambda x: x[1].get("position", 99) or 99)

    # Fastest lap holder
    fl_num, best_fl = None, float("inf")
    for n, lp in lap_map.items():
        d = lp.get("lap_duration") or float("inf")
        if d < best_fl:
            best_fl, fl_num = d, n

    lines = [f"SESSION: {session_label}"]

    if weather:
        lines.append(
            f"Weather: air {weather.get('air_temperature','?')}°C, "
            f"track {weather.get('track_temperature','?')}°C, "
            f"humidity {weather.get('humidity','?')}%, "
            f"{'WET/RAIN' if weather.get('rainfall') else 'dry'}"
        )

    lines.append("")
    lines.append("CURRENT ORDER (position, driver, team, gap to leader, interval to car ahead, tyre, tyre age, pit stops):")
    for n, pos_entry in sorted_drivers[:20]:
        info  = driver_map.get(n, {})
        name  = info.get("full_name") or f"#{n}"
        team  = info.get("team_name", "")
        pos   = pos_entry.get("position", "?")
        iv    = interval_map.get(n, {})
        gap   = iv.get("gap_to_leader")
        interval = iv.get("interval")
        gap_str = f"{gap:.1f}s" if isinstance(gap, (int, float)) else "—"
        int_str = f"{interval:.1f}s" if isinstance(interval, (int, float)) else "—"
        st_e  = stint_map.get(n, {})
        comp  = st_e.get("compound", "?")
        age   = st_e.get("tyre_age_at_end", "?")
        pits  = pit_count.get(n, 0)
        fl_marker = " [FASTEST LAP]" if n == fl_num else ""

        lines.append(
            f"  P{pos} {name} ({team}) — gap {gap_str}, interval {int_str}, "
            f"tyre {comp} ({age} laps old), {pits} pit stops{fl_marker}"
        )

    if last_pit:
        lines.append("")
        lines.append("RECENT PIT STOPS:")
        for n, ps in sorted(last_pit.items(), key=lambda x: x[1].get("date",""), reverse=True)[:8]:
            info = driver_map.get(n, {})
            name = info.get("full_name") or f"#{n}"
            lap  = ps.get("lap_number", "?")
            dur  = ps.get("pit_duration")
            dur_s = f"{dur:.1f}s" if isinstance(dur, (int, float)) else "?"
            lines.append(f"  {name}: lap {lap}, stop duration {dur_s}")

    if rc_messages:
        lines.append("")
        lines.append("RECENT RACE CONTROL MESSAGES (most recent first):")
        for msg in reversed(rc_messages[-10:]):
            cat  = msg.get("category", "")
            text = msg.get("message", "")
            lap  = msg.get("lap_number", "")
            lines.append(f"  [{cat}{f' lap {lap}' if lap else ''}] {text}")

    return "\n".join(lines)
