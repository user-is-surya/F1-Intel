"""
F1Intel — KPI Card Components
Renders animated glass KPI cards for the dashboard.
"""

from __future__ import annotations
import streamlit as st


def kpi_card(value: str, label: str, sub: str = "", icon: str = "",
             color: str = "#E10600", width_class: str = "") -> str:
    """Return HTML for a single KPI card."""
    icon_html = f'<div style="font-size:1.6rem;margin-bottom:0.3rem;">{icon}</div>' if icon else ""
    sub_html   = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    value_style = f"color:{color}" if color != "#FFFFFF" else ""
    return f"""
    <div class="kpi-card {width_class}">
        {icon_html}
        <div class="kpi-value" style="{value_style}">{value}</div>
        <div class="kpi-label">{label}</div>
        {sub_html}
    </div>
    """


def render_kpi_row(cards: list[dict], cols: int = 4) -> None:
    """
    Render a row of KPI cards.
    Each card dict: {value, label, sub?, icon?, color?}
    """
    columns = st.columns(min(cols, len(cards)))
    for i, (col, card) in enumerate(zip(columns, cards)):
        with col:
            st.markdown(kpi_card(
                value=str(card.get("value", "—")),
                label=card.get("label", ""),
                sub=card.get("sub", ""),
                icon=card.get("icon", ""),
                color=card.get("color", "#FFFFFF"),
            ), unsafe_allow_html=True)


def championship_leader_card(driver: dict, label: str = "Championship Leader") -> None:
    """Render a prominent leader card."""
    given  = driver.get("Driver", {}).get("givenName", "")
    family = driver.get("Driver", {}).get("familyName", "")
    team   = driver.get("Constructors", [{}])[0].get("name", "") if driver.get("Constructors") else ""
    points = driver.get("points", "0")
    wins   = driver.get("wins", "0")
    nationality = driver.get("Driver", {}).get("nationality", "")

    from utils.flags import get_flag, get_country_flag
    from config.teams import get_team_color
    from utils.helpers import driver_link_html
    constructor_id = driver.get("Constructors", [{}])[0].get("constructorId", "") if driver.get("Constructors") else ""
    team_color = get_team_color(constructor_id)
    driver_id  = driver.get("Driver", {}).get("driverId", "")
    name_html  = driver_link_html(
        f'{given} <span style="color:{team_color};">{family}</span>', driver_id
    )

    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid {team_color};position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;right:0;width:60px;height:60px;
                    background:radial-gradient(circle, {team_color}33, transparent);
                    border-radius:0 0 0 60px;"></div>
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.14em;color:var(--text-muted);margin-bottom:0.5rem;">
            🏆 {label}
        </div>
        <div style="font-size:1.5rem;font-weight:800;letter-spacing:-0.02em;">
            {get_flag(nationality)} {name_html}
        </div>
        <div style="font-size:0.82rem;color:var(--text-secondary);margin-top:0.2rem;">
            {team}
        </div>
        <div style="display:flex;gap:1.5rem;margin-top:0.8rem;">
            <div>
                <div style="font-size:1.6rem;font-weight:800;color:{team_color};">{points}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Points</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:800;">{wins}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Wins</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def constructor_leader_card(constructor: dict) -> None:
    """Render constructor championship leader card."""
    name   = constructor.get("Constructor", {}).get("name", "Unknown")
    cid    = constructor.get("Constructor", {}).get("constructorId", "")
    points = constructor.get("points", "0")
    wins   = constructor.get("wins", "0")

    from config.teams import get_team_color
    color = get_team_color(cid)

    from utils.flags import get_country_flag
    nationality = constructor.get("Constructor", {}).get("nationality", "")
    flag = get_country_flag(nationality)

    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid {color};">
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.14em;color:var(--text-muted);margin-bottom:0.5rem;">
            🏗️ Constructors Leader
        </div>
        <div style="font-size:1.5rem;font-weight:800;">
            {flag} <span style="color:{color};">{name}</span>
        </div>
        <div style="display:flex;gap:1.5rem;margin-top:0.8rem;">
            <div>
                <div style="font-size:1.6rem;font-weight:800;color:{color};">{points}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Points</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:800;">{wins}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Wins</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
