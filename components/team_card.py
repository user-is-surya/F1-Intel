"""
F1Intel — Team Card Component
Uses Streamlit native components — no raw HTML rendering issues.
"""
from __future__ import annotations
import streamlit as st
from config.teams import get_team_color
from utils.flags import get_country_flag
from utils.formatters import format_points


def render_team_profile(constructor: dict, standing: dict | None = None,
                         drivers: list[dict] | None = None) -> None:
    name       = constructor.get("name", "Unknown")
    cid        = constructor.get("constructorId", "")
    nat        = constructor.get("nationality", "")
    team_color = get_team_color(cid)
    flag       = get_country_flag(nat)
    points     = "—"
    position   = "—"
    wins       = "—"

    if standing:
        points   = format_points(standing.get("points", "0"))
        position = standing.get("position", "—")
        wins     = standing.get("wins", "0")

    # Colored top strip
    st.markdown(
        f'<div style="background:{team_color};border-radius:14px 14px 0 0;'
        f'padding:4px 16px;font-size:0.62rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.14em;color:var(--text-primary);">'
        f'{flag} {nat}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="padding:0.6rem 0 0.3rem;">'
        f'<div style="font-size:1.8rem;font-weight:900;letter-spacing:-0.02em;">'
        f'<span style="color:{team_color};">■</span> {name}</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Position", f"P{position}")
    with c2:
        st.metric("Points", points)
    with c3:
        st.metric("Wins", wins)

    if drivers:
        st.markdown(
            '<div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.12em;'
            'color:var(--text-muted);margin-top:0.5rem;margin-bottom:0.3rem;">Driver Lineup</div>',
            unsafe_allow_html=True,
        )
        for d in drivers[:2]:
            gname  = d.get("givenName", "")
            fname  = d.get("familyName", "")
            number = d.get("permanentNumber", "")
            st.markdown(
                f'<div style="padding:3px 0;font-size:0.85rem;">'
                f'<span style="color:{team_color};font-weight:700;font-family:\'JetBrains Mono\',monospace;'
                f'margin-right:8px;">#{number}</span>{gname} {fname}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
