"""
F1Intel — Driver Card Component
Uses Streamlit native components — no raw HTML rendering issues.
"""
from __future__ import annotations
import streamlit as st
from utils.flags import get_flag
from config.teams import get_team_color
from utils.helpers import driver_display_name, driver_link_html


def render_driver_profile(driver_info: dict, standing: dict | None = None,
                           season_stats: dict | None = None) -> None:
    given  = driver_info.get("givenName", "")
    family = driver_info.get("familyName", "")
    number = driver_info.get("permanentNumber", "—")
    nat    = driver_info.get("nationality", "")
    dob    = driver_info.get("dateOfBirth", "")
    flag   = get_flag(nat)

    team_name  = ""
    team_color = "#E10600"
    points     = "—"
    wins       = "—"
    position   = "—"

    if standing:
        constructors = standing.get("Constructors", [{}])
        if constructors:
            cid        = constructors[0].get("constructorId", "")
            team_name  = constructors[0].get("name", "")
            team_color = get_team_color(cid)
        points   = standing.get("points", "—")
        wins     = standing.get("wins", "—")
        position = standing.get("position", "—")

    age_str = ""
    if dob:
        try:
            from datetime import date
            birth = date.fromisoformat(dob)
            age   = (date.today() - birth).days // 365
            age_str = f"Age {age}"
        except Exception:
            pass

    # ── Header strip ──
    st.markdown(
        f'<div style="background:{team_color};border-radius:14px 14px 0 0;'
        f'padding:4px 16px;font-size:0.62rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.14em;color:var(--text-primary);">'
        f'{flag} {nat} · {team_name}</div>',
        unsafe_allow_html=True,
    )

    age_html = (f'<div style="font-size:0.78rem;color:var(--text-muted);'
                f'margin-top:4px;">{age_str}</div>' if age_str else "")

    col_name, col_num = st.columns([3, 1])
    with col_name:
        st.markdown(
            f'<div style="padding:0.8rem 0 0.2rem;">'
            f'<div style="font-size:1.6rem;font-weight:300;letter-spacing:-0.01em;">{given}</div>'
            f'<div style="font-size:2rem;font-weight:900;letter-spacing:-0.03em;'
            f'color:{team_color};line-height:1;">{family.upper()}</div>'
            f'{age_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_num:
        st.markdown(
            f'<div style="font-size:3.5rem;font-weight:900;color:{team_color};'
            f'opacity:0.25;text-align:right;padding-top:0.5rem;'
            f'font-family:\'JetBrains Mono\',monospace;line-height:1;">{number}</div>',
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Championship", f"P{position}")
    with c2:
        st.metric("Points", points)
    with c3:
        st.metric("Wins", wins)


def render_driver_mini(driver: dict, standing: dict | None = None) -> None:
    given  = driver.get("givenName", "")
    family = driver.get("familyName", "")
    nat    = driver.get("nationality", "")
    number = driver.get("permanentNumber", "")
    driver_id = driver.get("driverId", "")
    flag   = get_flag(nat)
    team_color = "#E10600"
    team_name  = ""
    points     = "—"

    if standing:
        constructors = standing.get("Constructors", [{}])
        if constructors:
            cid        = constructors[0].get("constructorId", "")
            team_name  = constructors[0].get("name", "")
            team_color = get_team_color(cid)
        points = standing.get("points", "—")

    name_html = driver_link_html(f"{given} {family}", driver_id)
    st.markdown(
        f'<div class="glass-card" style="padding:0.7rem 1rem;border-left:3px solid {team_color};">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<div><div style="font-weight:700;font-size:0.9rem;">{flag} {name_html}</div>'
        f'<div style="font-size:0.72rem;color:var(--text-muted);">{team_name}</div></div>'
        f'<div style="text-align:right;">'
        f'<div style="font-weight:800;color:{team_color};">{points} pts</div>'
        f'<div style="font-size:0.7rem;color:var(--text-muted);font-family:\'JetBrains Mono\',monospace;">#{number}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )
