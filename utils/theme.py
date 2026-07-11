"""
F1Intel — Theme State
Single source of truth for dark/light mode.

Design notes (why this replaces the old JS floating-toggle approach):
  - The previous implementation injected a <script> via components.html()
    that set inline CSS variables on window.parent.document and re-injected
    a second competing <style> block, polling with setInterval every 2s.
    That's slow (a full iframe per page, forever), and fragile — the two
    dark/light variable maps had a copy-paste bug where "light" mode still
    listed the dark mode's white text colors, which is exactly why the
    dashboard/tables were unreadable in light mode.
  - Here, theme is just a plain Streamlit value living in st.query_params
    (?theme=dark|light), mirrored into st.session_state. Python fully knows
    the active theme on every rerun, so:
      * CSS is emitted with the *correct* variables already substituted in
        (no attribute-matching race, no JS needed at all).
      * Plotly figures (which cannot read CSS variables) can pick the right
        literal colors too, via get_plotly_colors().
    It's also a plain Streamlit button, so no extra iframe/component cost.
"""
from __future__ import annotations
import streamlit as st

DEFAULT_THEME = "dark"


def get_theme() -> str:
    """Return the active theme ('dark' or 'light'), resolving query param -> session_state -> default."""
    if "theme" in st.session_state:
        current = st.session_state["theme"]
    else:
        current = st.query_params.get("theme", DEFAULT_THEME)
        if current not in ("dark", "light"):
            current = DEFAULT_THEME
        st.session_state["theme"] = current
    return current


def set_theme(theme: str) -> None:
    st.session_state["theme"] = theme
    st.query_params["theme"] = theme


def toggle_theme() -> None:
    set_theme("light" if get_theme() == "dark" else "dark")


def render_theme_toggle() -> None:
    """Compact icon toggle for the sidebar footer."""
    theme = get_theme()
    label = "☀️ Light mode" if theme == "dark" else "🌙 Dark mode"
    if st.button(label, key="theme_toggle_btn", width="stretch"):
        toggle_theme()
        st.rerun()
