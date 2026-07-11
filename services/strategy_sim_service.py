"""
F1Intel — Strategy Simulator Engine
Pure data-driven simulation: derives per-compound degradation curves from a
driver's REAL lap data in a given race, then re-projects lap times under an
alternate pit strategy to estimate a resulting finishing position/time delta.

No AI/LLM involved — this is deterministic math built directly from FastF1
lap and tire data. Estimates are clearly approximate (see ASSUMPTIONS).

ASSUMPTIONS (surfaced to the user in the UI, not hidden):
  - Pit stop time loss is a fixed average (typical ~20-25s) rather than the
    exact value for that circuit's pit lane.
  - No modeling of traffic, overtaking difficulty, or safety car timing —
    the simulation assumes a clear track.
  - Degradation curve is fit per-driver from THAT race only (their own car/
    tire management), using a simple linear (or quadratic if enough data)
    regression on lap time vs tyre age, per compound.
  - If a compound wasn't used by the driver in the real race, we fall back
    to the FIELD-AVERAGE degradation curve for that compound (computed
    across all drivers in the session) so the what-if can still explore
    compounds the driver didn't actually run.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st

# Typical pit lane time loss in seconds (stationary time + in/out lap delta).
# This is a reasonable average across circuits — not circuit-specific.
DEFAULT_PIT_LOSS_SECONDS = 22.0

VALID_COMPOUNDS = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]


def _clean_lap_seconds(laps: pd.DataFrame) -> pd.DataFrame:
    """Return laps with a numeric LapSec column, outliers (safety car / pit laps) removed."""
    if laps.empty or "LapTime" not in laps.columns:
        return pd.DataFrame()
    df = laps.copy()
    df["LapSec"] = df["LapTime"].dt.total_seconds()
    df = df.dropna(subset=["LapSec", "Compound", "TyreLife"])
    if df.empty:
        return df
    # Remove obvious outliers (in/out laps, safety car laps) — anything more
    # than 8% slower than that driver's median lap is excluded from the fit.
    median = df["LapSec"].median()
    df = df[df["LapSec"] < median * 1.08]
    return df


def fit_degradation_curve(laps: pd.DataFrame, driver: str, compound: str) -> dict | None:
    """
    Fit lap_time = a + b*tyre_age (+ c*tyre_age^2 if enough points) for one
    driver on one compound, using their real laps from this session.
    Returns dict with base_time, deg_per_lap, deg_accel, n_points — or None
    if there isn't enough real data for this driver+compound combination.
    """
    df = _clean_lap_seconds(laps)
    if df.empty:
        return None
    sub = df[(df["Driver"] == driver) & (df["Compound"].str.upper() == compound.upper())]
    if len(sub) < 3:
        return None

    x = sub["TyreLife"].astype(float).values
    y = sub["LapSec"].astype(float).values

    try:
        if len(sub) >= 6:
            # Quadratic fit captures accelerating degradation (cliff effect)
            coeffs = np.polyfit(x, y, 2)
            c, b, a = coeffs[0], coeffs[1], coeffs[2]
        else:
            coeffs = np.polyfit(x, y, 1)
            b, a = coeffs[0], coeffs[1]
            c = 0.0
        return {
            "base_time": float(a), "deg_per_lap": float(b), "deg_accel": float(c),
            "n_points": len(sub), "source": "driver",
        }
    except Exception:
        return None


def fit_field_average_curve(laps: pd.DataFrame, compound: str) -> dict | None:
    """Fallback: fit the degradation curve using ALL drivers' laps on this
    compound in the session, for when a specific driver never ran that tyre."""
    df = _clean_lap_seconds(laps)
    if df.empty:
        return None
    sub = df[df["Compound"].str.upper() == compound.upper()]
    if len(sub) < 5:
        return None

    x = sub["TyreLife"].astype(float).values
    y = sub["LapSec"].astype(float).values
    try:
        coeffs = np.polyfit(x, y, 2 if len(sub) >= 10 else 1)
        if len(coeffs) == 3:
            c, b, a = coeffs
        else:
            b, a = coeffs
            c = 0.0
        return {
            "base_time": float(a), "deg_per_lap": float(b), "deg_accel": float(c),
            "n_points": len(sub), "source": "field_average",
        }
    except Exception:
        return None


def get_driver_compounds_used(laps: pd.DataFrame, driver: str) -> list[str]:
    """List compounds this driver actually ran in the race."""
    if laps.empty or "Compound" not in laps.columns:
        return []
    sub = laps[laps["Driver"] == driver]
    return sorted(sub["Compound"].dropna().str.upper().unique().tolist())


def project_lap_time(curve: dict, tyre_age: int) -> float:
    """Project a single lap time at a given tyre age using a fitted curve."""
    a, b, c = curve["base_time"], curve["deg_per_lap"], curve.get("deg_accel", 0.0)
    return a + b * tyre_age + c * (tyre_age ** 2)


def get_real_stint_plan(stints: pd.DataFrame, driver: str) -> list[dict]:
    """Return the driver's actual stint plan as a list of
    {stint, compound, first_lap, last_lap, laps} dicts, ordered by stint."""
    if stints.empty:
        return []
    sub = stints[stints["Driver"] == driver].sort_values("Stint")
    return sub.to_dict("records")


def simulate_alternate_strategy(
    laps: pd.DataFrame,
    stints: pd.DataFrame,
    driver: str,
    total_race_laps: int,
    new_stint_plan: list[dict],
    pit_loss_seconds: float = DEFAULT_PIT_LOSS_SECONDS,
) -> dict:
    """
    Re-simulate a driver's race time under an alternate stint plan.

    new_stint_plan: list of {"compound": "MEDIUM", "start_lap": 1, "end_lap": 18}
                     covering laps 1..total_race_laps with no gaps.

    Returns:
      {
        "total_time": float seconds,
        "lap_times": list of per-lap projected times,
        "pit_stops": int,
        "curves_used": {compound: curve_dict, ...},
        "warnings": [str, ...],
      }
    """
    warnings: list[str] = []
    curves_used: dict[str, dict] = {}
    lap_times: list[float] = []
    total_time = 0.0
    pit_stops = max(0, len(new_stint_plan) - 1)

    driver_compounds = set(get_driver_compounds_used(laps, driver))

    for stint in new_stint_plan:
        compound = stint["compound"].upper()
        start_lap = stint["start_lap"]
        end_lap = stint["end_lap"]
        stint_len = end_lap - start_lap + 1
        if stint_len <= 0:
            continue

        curve = None
        if compound in driver_compounds:
            curve = fit_degradation_curve(laps, driver, compound)
        if curve is None:
            curve = fit_field_average_curve(laps, compound)
            if curve is not None:
                warnings.append(
                    f"No real {compound} data for this driver — using field-average "
                    f"degradation curve for {compound} instead."
                )
        if curve is None:
            warnings.append(
                f"Not enough data to model {compound} tyres in this session — "
                f"stint estimated using overall race-average pace."
            )
            overall = _clean_lap_seconds(laps)
            fallback_base = float(overall["LapSec"].median()) if not overall.empty else 90.0
            curve = {"base_time": fallback_base, "deg_per_lap": 0.05, "deg_accel": 0.0,
                      "n_points": 0, "source": "fallback"}

        curves_used[compound] = curve

        for tyre_age in range(stint_len):
            lt = project_lap_time(curve, tyre_age)
            lap_times.append(lt)
            total_time += lt

    # Add pit stop time loss for each stop (not counted on the final stint)
    total_time += pit_stops * pit_loss_seconds

    return {
        "total_time": total_time,
        "lap_times": lap_times,
        "pit_stops": pit_stops,
        "curves_used": curves_used,
        "warnings": warnings,
    }


def get_actual_race_time(laps: pd.DataFrame, driver: str) -> float | None:
    """Sum of this driver's REAL lap times in the race, for comparison baseline."""
    df = laps[laps["Driver"] == driver].copy()
    if df.empty or "LapTime" not in df.columns:
        return None
    df["LapSec"] = df["LapTime"].dt.total_seconds()
    df = df.dropna(subset=["LapSec"])
    if df.empty:
        return None
    return float(df["LapSec"].sum())


def estimate_position_change(
    all_laps: pd.DataFrame,
    driver: str,
    simulated_total_time: float,
    actual_total_time: float,
) -> dict:
    """
    Estimate the finishing-position effect of a time delta by comparing
    against the actual race gaps between drivers (from real lap data).
    This is a simplified model: it shifts the driver's finishing time and
    checks how many other drivers' actual total times it would now be
    ahead of / behind, assuming no other driver's race changes.
    """
    delta = simulated_total_time - actual_total_time  # negative = faster

    all_totals: dict[str, float] = {}
    for drv in all_laps["Driver"].dropna().unique():
        t = get_actual_race_time(all_laps, drv)
        if t is not None:
            all_totals[drv] = t

    if driver not in all_totals or not all_totals:
        return {"delta_seconds": delta, "estimated_position": None,
                "actual_position_by_time": None, "field_size": 0}

    sorted_drivers = sorted(all_totals.items(), key=lambda x: x[1])
    actual_rank = next((i + 1 for i, (d, _) in enumerate(sorted_drivers) if d == driver), None)

    new_time = all_totals[driver] + delta
    # Recompute rank with this driver's time swapped for the simulated one
    other_totals = {d: t for d, t in all_totals.items() if d != driver}
    new_rank = 1 + sum(1 for t in other_totals.values() if t < new_time)

    return {
        "delta_seconds": delta,
        "estimated_position": new_rank,
        "actual_position_by_time": actual_rank,
        "field_size": len(all_totals),
    }
