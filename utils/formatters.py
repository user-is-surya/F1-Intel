"""
F1Intel — Formatter Utilities
Consistent time/lap/sector/delta string formatting.
"""

from __future__ import annotations
import pandas as pd
from datetime import timedelta
from typing import Optional


def format_laptime(td: Optional[timedelta | pd.Timedelta | float]) -> str:
    """Format a timedelta or float (seconds) as M:SS.mmm"""
    if td is None or (isinstance(td, float) and pd.isna(td)):
        return "—"
    try:
        if isinstance(td, (int, float)):
            total = float(td)
        else:
            total = td.total_seconds()
        if pd.isna(total) or total <= 0:
            return "—"
        mins = int(total // 60)
        secs = total % 60
        return f"{mins}:{secs:06.3f}"
    except Exception:
        return "—"


def format_sector(td: Optional[timedelta | pd.Timedelta | float]) -> str:
    """Format sector time as SS.mmm"""
    if td is None:
        return "—"
    try:
        if isinstance(td, (int, float)):
            total = float(td)
        else:
            total = td.total_seconds()
        if pd.isna(total) or total <= 0:
            return "—"
        return f"{total:.3f}s"
    except Exception:
        return "—"


def format_gap(gap: Optional[float | str]) -> str:
    """Format interval gap as +0.000 or +1 lap."""
    if gap is None or gap == "" or (isinstance(gap, float) and pd.isna(gap)):
        return "—"
    if isinstance(gap, str):
        return gap
    if gap == 0:
        return "Leader"
    return f"+{gap:.3f}s"


def format_delta(delta_seconds: float) -> str:
    """Format a delta time (positive = slower, negative = faster)."""
    if pd.isna(delta_seconds):
        return "—"
    sign = "+" if delta_seconds >= 0 else ""
    return f"{sign}{delta_seconds:.3f}s"


def seconds_to_laptime(seconds: float) -> str:
    """Convert raw seconds float to lap time string."""
    return format_laptime(seconds)


def format_points(pts: str | float | int) -> str:
    try:
        v = float(pts)
        if v == int(v):
            return str(int(v))
        return f"{v:.1f}"
    except Exception:
        return str(pts)


def ordinal(n: int) -> str:
    """Return ordinal string: 1st, 2nd, 3rd..."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_date(date_str: str, fmt: str = "%d %b %Y") -> str:
    """Parse ISO date string and reformat."""
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime(fmt)
    except Exception:
        return date_str


def format_speed(speed_ms: float) -> str:
    """Convert m/s to km/h and format."""
    return f"{speed_ms * 3.6:.0f} km/h"


def tire_age_label(laps: int) -> str:
    if laps == 0:
        return "New"
    return f"{laps}L"
