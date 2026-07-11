"""
F1Intel — Circuit Card Component
Uses Streamlit native components — no raw HTML rendering issues.
"""
from __future__ import annotations
import streamlit as st
from utils.flags import get_country_flag
from utils.formatters import format_date


def render_circuit_card(circuit: dict, race: dict | None = None) -> None:
    name    = circuit.get("circuitName", "Unknown Circuit")
    loc     = circuit.get("Location", {})
    country = loc.get("country", "")
    city    = loc.get("locality", "")
    flag    = get_country_flag(country)
    race_name = race.get("raceName", "") if race else ""
    race_date = race.get("date", "")     if race else ""
    date_fmt  = format_date(race_date)   if race_date else ""

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(
            f'<div><div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.14em;'
            f'color:var(--text-muted);">{flag} {country}</div>'
            f'<div style="font-size:1.4rem;font-weight:800;margin:2px 0;">{name}</div>'
            f'<div style="font-size:0.82rem;color:var(--text-secondary);">{city}</div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        if race_name:
            st.markdown(
                f'<div style="text-align:right;">'
                f'<div style="font-size:0.9rem;font-weight:600;color:#E10600;">{race_name}</div>'
                f'<div style="font-size:0.78rem;color:var(--text-muted);">{date_fmt}</div></div>',
                unsafe_allow_html=True,
            )


def render_circuit_stats_card(stats: dict) -> None:
    items = [
        ("🏁", "Lap Record",   stats.get("lap_record",  "—")),
        ("📏", "Track Length", stats.get("length",       "—")),
        ("↩️", "Corners",      stats.get("corners",      "—")),
        ("💨", "DRS Zones",    stats.get("drs_zones",    "—")),
        ("🏆", "First GP",     stats.get("first_gp",     "—")),
        ("📅", "Race Laps",    stats.get("race_laps",    "—")),
    ]
    cols = st.columns(len(items))
    for col, (icon, label, value) in zip(cols, items):
        with col:
            st.metric(label=f"{icon} {label}", value=value)
