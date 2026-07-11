"""
F1Intel — Miscellaneous Helpers
"""

from __future__ import annotations
import streamlit as st
import os
from pathlib import Path
from typing import Any

from utils.theme import get_theme

_CSS_FILE_CACHE: dict[str, str] = {}


def _read_css_file(path: str) -> str:
    """Read+cache the static stylesheet contents (the file itself doesn't
    change at runtime, only the variables layered on top of it do)."""
    if path not in _CSS_FILE_CACHE:
        with open(path) as f:
            _CSS_FILE_CACHE[path] = f.read()
    return _CSS_FILE_CACHE[path]


def load_css(path: str | None = None) -> None:
    """
    Inject the global stylesheet PLUS a `:root { ... }` block with the
    current theme's variable values already substituted in.

    This is the entire theme system: no JS, no localStorage polling, no
    second competing <style> tag. Python resolves the active theme
    (utils.theme.get_theme, backed by a query param) and writes the exact
    variable values directly into the page on every render, so there's
    never a mismatch between what the toggle says and what's on screen.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")

    theme = get_theme()
    from config.settings import get_theme_css_vars
    variables = get_theme_css_vars(theme)
    var_block = "\n".join(f"    {k}: {v};" for k, v in variables.items())

    css = ""
    if os.path.exists(path):
        css = _read_css_file(path)

    st.markdown(
        f"<style>\n:root {{\n{var_block}\n}}\n{css}\n</style>",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a standard F1Intel page header."""
    title_text = f"{icon} {title}" if icon else title
    st.markdown(f"""
    <div class="page-header fade-in">
        <h1 class="page-title">{title_text}</h1>
        {f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ''}
        <div class="accent-line"></div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str) -> None:
    """Render a small section header with red dot."""
    st.markdown(f"""
    <div class="section-header">
        <div class="section-dot"></div>
        <span class="section-title">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def divider() -> None:
    st.markdown('<hr class="f1-divider">', unsafe_allow_html=True)


def glass_card(content_html: str, extra_class: str = "") -> None:
    st.markdown(f'<div class="glass-card {extra_class}">{content_html}</div>',
                unsafe_allow_html=True)


def status_badge(label: str, status: str = "live") -> str:
    """Return HTML for a status badge. status: 'live' | 'upcoming' | 'finished' | 'funding'"""
    return f'<span class="status-badge status-{status}">{label}</span>'


def tire_badge_html(compound: str) -> str:
    compound = compound.upper() if compound else "UNKNOWN"
    letter = {"SOFT": "S", "MEDIUM": "M", "HARD": "H",
               "INTER": "I", "WET": "W"}.get(compound, "?")
    cls = {"SOFT": "soft", "MEDIUM": "medium", "HARD": "hard",
           "INTER": "inter", "WET": "wet"}.get(compound, "")
    return f'<span class="tire-badge tire-{cls}">{letter}</span>'


def get_asset_path(filename: str) -> str:
    """Return absolute path to an asset file."""
    base = Path(__file__).parent.parent / "assets"
    return str(base / filename)


def safe_get(data: dict, *keys, default: Any = None) -> Any:
    """Safely navigate nested dicts."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
        if data is None:
            return default
    return data


def driver_display_name(driver: dict) -> str:
    """Return formatted display name from Jolpica driver dict."""
    given = driver.get("givenName", "")
    family = driver.get("familyName", "")
    return f"{given} {family}".strip()


def driver_link_html(display_text: str, driver_id: str, extra_style: str = "") -> str:
    """
    Wrap text in an anchor that navigates to the Drivers page profile for
    this driver_id. Safe to embed inside larger HTML blocks built with
    st.markdown(unsafe_allow_html=True) — e.g. standings rows, race result
    tables — since it's just a plain <a> tag, not a Streamlit widget.

    Uses a relative URL ("drivers?driver=<id>") which Streamlit's
    multipage router resolves correctly regardless of how the app is
    mounted (works the same on localhost and when deployed).
    """
    if not driver_id:
        return display_text
    return (
        f'<a href="drivers?driver={driver_id}" target="_self" '
        f'style="color:inherit;text-decoration:none;cursor:pointer;{extra_style}" '
        f'onmouseover="this.style.textDecoration=\'underline\'" '
        f'onmouseout="this.style.textDecoration=\'none\'">{display_text}</a>'
    )


def constructor_display_name(constructor: dict) -> str:
    return constructor.get("name", constructor.get("constructorId", "Unknown"))


def round_label(race: dict) -> str:
    """Return 'Round X — Grand Prix Name'."""
    rnd = race.get("round", "?")
    name = race.get("raceName", "Unknown")
    return f"Round {rnd} — {name}"


def make_plotly_layout(title: str = "", height: int = 400, theme: str | None = None) -> dict:
    """
    Return a theme-aware Plotly layout dict. Plotly can't read CSS
    variables (it draws literal colors, not cascaded styles), so this
    pulls the matching literal palette from config.settings.THEMES for
    whichever theme is currently active, keeping charts in sync with the
    rest of the UI instead of going white-on-white in light mode.
    """
    from config.settings import get_theme_plotly
    if theme is None:
        theme = get_theme()
    p = get_theme_plotly(theme)
    return {
        "title":       {"text": title, "font": {"color": p["font"], "size": 14}},
        "paper_bgcolor": p["paper_bg"],
        "plot_bgcolor":  p["plot_bg"],
        "font":          {"color": p["font"], "family": "Inter, sans-serif"},
        "xaxis":         {"gridcolor": p["grid"], "linecolor": p["grid"], "zerolinecolor": p["grid"]},
        "yaxis":         {"gridcolor": p["grid"], "linecolor": p["grid"], "zerolinecolor": p["grid"]},
        "height":        height,
        "margin":        {"l": 40, "r": 20, "t": 40, "b": 40},
        "legend":        {"bgcolor": "rgba(0,0,0,0)", "font": {"color": p["font"]}},
        "hoverlabel":    {"bgcolor": p["hover_bg"], "font": {"color": p["hover_font"]}},
    }
