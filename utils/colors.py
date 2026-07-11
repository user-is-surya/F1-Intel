"""
F1Intel — Color Utilities
Team colors, gradient generation, and Plotly palette helpers.
"""

from __future__ import annotations
from config.teams import get_team_color


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert #RRGGBB hex to rgba() string."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def get_team_rgba(constructor_id: str, alpha: float = 1.0) -> str:
    return hex_to_rgba(get_team_color(constructor_id), alpha)


def position_color(pos: int) -> str:
    """Return color for a finishing position."""
    if pos == 1:   return "#FFD700"
    if pos == 2:   return "#C0C0C0"
    if pos == 3:   return "#CD7F32"
    if pos <= 10:  return "#4CAF50"
    return "#888888"


def delta_color(value: float) -> str:
    """Green for positive, red for negative delta."""
    if value > 0:  return "#4CAF50"
    if value < 0:  return "#E10600"
    return "#888888"


def compound_color(compound: str) -> str:
    from config.settings import TIRE_COLORS
    return TIRE_COLORS.get(compound.upper(), "#888888")


def build_driver_color_map(drivers: list[str], session=None) -> dict[str, str]:
    """
    Build {driver_abbr: hex_color} map.
    Uses FastF1 TeamColor if session is provided.
    """
    colors: dict[str, str] = {}
    fallback = [
        "#E10600", "#00D2BE", "#FF8700", "#3671C6", "#006F62",
        "#0093CC", "#64C4FF", "#6692FF", "#52E252", "#B6BABD",
        "#C92D4B", "#FFF500", "#4CAF50", "#9C27B0", "#FF5722",
        "#00BCD4", "#8BC34A", "#FF9800", "#607D8B", "#795548",
    ]
    for i, drv in enumerate(drivers):
        if session:
            try:
                info = session.get_driver(drv)
                tc = info.get("TeamColor", "")
                if tc:
                    colors[drv] = f"#{tc}"
                    continue
            except Exception:
                pass
        colors[drv] = fallback[i % len(fallback)]
    return colors


def championship_gradient(n: int) -> list[str]:
    """Return n colors for a standings chart (red → faded)."""
    base = [
        "#E10600", "#FF4444", "#FF7744", "#FFAA00",
        "#FFD700", "#CCCC00", "#99CC00", "#66BB6A",
        "#42A5F5", "#AB47BC",
    ]
    return [base[i % len(base)] for i in range(n)]


def hex_alpha(hex_color: str, alpha_hex: str = "33") -> str:
    """Convert #RRGGBB + 2-char hex alpha → rgba() string Plotly accepts.
    e.g. hex_alpha('#E10600', '33') → 'rgba(225,6,0,0.2)'
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    if len(h) < 6:
        return "rgba(128,128,128,0.2)"
    try:
        r = int(h[0:2],16)
        g = int(h[2:4],16)
        b = int(h[4:6],16)
        a = round(int(alpha_hex,16)/255, 2)
        return f"rgba({r},{g},{b},{a})"
    except Exception:
        return "rgba(128,128,128,0.2)"
