"""
F1Intel — Race Story Data Aggregator
Gathers everything needed to write a rich race story: race results,
qualifying, sprint (if held), pit stops, fastest lap, and brief
historical context for the circuit — then formats it as a compact,
structured text block ready to hand to the AI for narrative generation.

This is pure data plumbing, no AI calls here — keeps the prompt-building
testable and separate from the LLM interaction itself.
"""

from __future__ import annotations
from services.jolpica_service import (
    get_race_results, get_qualifying_results, get_sprint_results,
    get_pit_stops, get_fastest_laps, get_circuit_history,
)
from utils.formatters import format_date


def _format_results_block(results: list[dict], label: str) -> str:
    if not results:
        return f"{label}: no data available.\n"
    lines = [f"{label}:"]
    for r in results[:10]:  # top 10 is plenty of narrative material
        pos    = r.get("position", "?")
        drv    = r.get("Driver", {})
        constr = r.get("Constructor", {})
        name   = f"{drv.get('givenName','')} {drv.get('familyName','')}".strip()
        team   = constr.get("name", "")
        status = r.get("status", "")
        pts    = r.get("points", "0")
        time_v = r.get("Time", {}).get("time", "") if r.get("Time") else ""
        grid   = r.get("grid", "")
        fl     = r.get("FastestLap", {})
        fl_rank = fl.get("rank", "") if fl else ""
        fl_marker = " [FASTEST LAP]" if fl_rank == "1" else ""
        time_or_status = time_v or status
        lines.append(
            f"  P{pos} (started P{grid}): {name} ({team}) — {time_or_status}, "
            f"{pts} pts{fl_marker}"
        )
    return "\n".join(lines) + "\n"


def _format_qualifying_block(qual: list[dict]) -> str:
    if not qual:
        return "Qualifying: no data available.\n"
    lines = ["Qualifying (top 10):"]
    for r in qual[:10]:
        pos  = r.get("position", "?")
        drv  = r.get("Driver", {})
        name = f"{drv.get('givenName','')} {drv.get('familyName','')}".strip()
        q3   = r.get("Q3") or r.get("Q2") or r.get("Q1") or "—"
        lines.append(f"  P{pos}: {name} — {q3}")
    return "\n".join(lines) + "\n"


def _format_pit_stops_block(pits: list[dict]) -> str:
    if not pits:
        return ""
    # Highlight the fastest and slowest stops, plus any multi-stop drivers
    def parse_dur(d):
        try:
            s = str(d)
            if ":" in s:
                m, sec = s.split(":")
                return float(m) * 60 + float(sec)
            return float(s)
        except Exception:
            return None

    durs = [(p, parse_dur(p.get("duration"))) for p in pits]
    durs = [(p, d) for p, d in durs if d is not None]
    if not durs:
        return ""
    fastest = min(durs, key=lambda x: x[1])
    slowest = max(durs, key=lambda x: x[1])

    stop_counts: dict[str, int] = {}
    for p in pits:
        did = p.get("driverId", "")
        stop_counts[did] = stop_counts.get(did, 0) + 1
    most_stops = max(stop_counts.items(), key=lambda x: x[1]) if stop_counts else None

    lines = ["Pit stops:"]
    lines.append(f"  Fastest stop: {fastest[0].get('driverId','')} — {fastest[1]:.2f}s (lap {fastest[0].get('lap','?')})")
    lines.append(f"  Slowest stop: {slowest[0].get('driverId','')} — {slowest[1]:.2f}s (lap {slowest[0].get('lap','?')})")
    if most_stops and most_stops[1] >= 3:
        lines.append(f"  Most stops: {most_stops[0]} made {most_stops[1]} pit stops")
    return "\n".join(lines) + "\n"


def _format_historical_block(history: list[dict], circuit_name: str) -> str:
    if not history:
        return ""
    lines = [f"Recent winners at {circuit_name}:"]
    for race in history[:5]:
        year    = race.get("season", "")
        results = race.get("Results", [])
        if not results:
            continue
        winner = results[0]
        drv    = winner.get("Driver", {})
        name   = f"{drv.get('givenName','')} {drv.get('familyName','')}".strip()
        lines.append(f"  {year}: {name}")
    return "\n".join(lines) + "\n" if len(lines) > 1 else ""


def build_race_story_context(season: int, race: dict) -> dict:
    """
    Gather all data needed for a race story into a structured dict.
    Returns:
      {
        "race_name": str, "circuit_name": str, "country": str, "date": str,
        "round": str, "has_sprint": bool,
        "context_text": str  <- the formatted block ready for the AI prompt
      }
    """
    round_num    = race.get("round", "")
    race_name    = race.get("raceName", "")
    circuit      = race.get("Circuit", {})
    circuit_name = circuit.get("circuitName", "")
    circuit_id   = circuit.get("circuitId", "")
    country      = circuit.get("Location", {}).get("country", "")
    date_str     = race.get("date", "")
    has_sprint   = bool(race.get("Sprint"))

    results  = get_race_results(season, round_num)
    qual     = get_qualifying_results(season, round_num)
    sprint   = get_sprint_results(season, round_num) if has_sprint else []
    pits     = get_pit_stops(season, round_num)
    history  = get_circuit_history(circuit_id, limit=6) if circuit_id else []

    parts = [
        f"RACE: {race_name}, Round {round_num}, {season} season",
        f"CIRCUIT: {circuit_name}, {country}",
        f"DATE: {format_date(date_str)}",
        "",
        _format_qualifying_block(qual),
    ]
    if sprint:
        parts.append(_format_results_block(sprint, "Sprint Results (top 10)"))
    parts.append(_format_results_block(results, "Race Results (top 10)"))
    pit_block = _format_pit_stops_block(pits)
    if pit_block:
        parts.append(pit_block)
    hist_block = _format_historical_block(history, circuit_name)
    if hist_block:
        parts.append(hist_block)

    context_text = "\n".join(p for p in parts if p)

    return {
        "race_name": race_name,
        "circuit_name": circuit_name,
        "country": country,
        "date": date_str,
        "round": round_num,
        "has_sprint": has_sprint,
        "context_text": context_text,
    }
