"""
F1Intel — Standings Center
Full driver & constructor standings with analytics.
"""

import streamlit as st
from config.teams import get_team_color
st.set_page_config(page_title="Standings — F1Intel", page_icon="🏆", layout="wide")

from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.standings_table import render_driver_standings, render_constructor_standings
from services.jolpica_service import (
    get_latest_standings, get_latest_constructor_standings,
    get_driver_standings, get_constructor_standings, get_schedule, get_race_results
)
from config.settings import CURRENT_SEASON
import plotly.graph_objects as go

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Standings Center", "Driver & Constructor Championship", "🏆")

driver_standings      = get_driver_standings(season)
constructor_standings = get_constructor_standings(season)
schedule              = get_schedule(season)

tab1, tab2, tab3 = st.tabs(["🏅 Driver Championship", "🏗️ Constructor Championship", "📊 Analytics"])

# ── Tab 1: Driver Standings ────────────────────────────────────────────────
with tab1:
    section_header("Driver Championship Standings")
    render_driver_standings(driver_standings)

    if len(driver_standings) >= 2:
        divider()
        section_header("Points Gap Analysis")

        names  = [s.get("Driver", {}).get("familyName", "") for s in driver_standings]
        points = [float(s.get("points", 0)) for s in driver_standings]
        leader = points[0] if points else 0
        gaps   = [leader - p for p in points]

        from config.teams import get_team_color
        colors = [
            get_team_color(
                s.get("Constructors", [{}])[0].get("constructorId", "")
                if s.get("Constructors") else ""
            )
            for s in driver_standings
        ]

        fig = go.Figure(go.Bar(
            x=names, y=gaps,
            marker=dict(color=colors, line=dict(color="rgba(0,0,0,0.3)", width=1)),
            hovertemplate="%{x}<br>Gap: -%{y:.0f} pts<extra></extra>",
        ))
        layout = make_plotly_layout("Points Gap from Championship Leader", height=350)
        layout["xaxis"]["tickangle"] = -30
        layout["yaxis"]["title"]     = "Points Behind Leader"
        layout["yaxis"]["autorange"] = "reversed"
        fig.update_layout(**layout)
        st.plotly_chart(fig, width='stretch')


# ── Tab 2: Constructor Standings ───────────────────────────────────────────
with tab2:
    section_header("Constructor Championship Standings")
    render_constructor_standings(constructor_standings)

    if len(constructor_standings) >= 2:
        divider()
        section_header("Constructor Points Comparison")

        con_names  = [s.get("Constructor", {}).get("name", "") for s in constructor_standings]
        con_points = [float(s.get("points", 0)) for s in constructor_standings]
        con_colors = [
            get_team_color(s.get("Constructor", {}).get("constructorId", ""))
            for s in constructor_standings
        ]

        fig2 = go.Figure(go.Bar(
            x=con_names, y=con_points,
            marker=dict(color=con_colors, line=dict(color="rgba(0,0,0,0.3)", width=1)),
            hovertemplate="%{x}: %{y:.0f} pts<extra></extra>",
        ))
        layout2 = make_plotly_layout("Constructor Points", height=350)
        layout2["xaxis"]["tickangle"] = -30
        layout2["yaxis"]["title"]     = "Points"
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, width='stretch')


# ── Tab 3: Analytics ───────────────────────────────────────────────────────
with tab3:
    section_header("Season Comparison Tool")

    col1, col2 = st.columns(2)
    with col1:
        season_a = st.selectbox("Season A", range(CURRENT_SEASON, 2017, -1), index=0, key="sa")
    with col2:
        season_b = st.selectbox("Season B", range(CURRENT_SEASON, 2017, -1), index=1, key="sb")

    if st.button("Compare Seasons"):
        with st.spinner("Loading comparison data…"):
            standings_a = get_driver_standings(season_a)
            standings_b = get_driver_standings(season_b)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{season_a} Driver Standings**")
            render_driver_standings(standings_a)
        with c2:
            st.markdown(f"**{season_b} Driver Standings**")
            render_driver_standings(standings_b)

    divider()
    section_header("Wins Distribution")

    if driver_standings:
        win_names  = [s.get("Driver", {}).get("familyName", "") for s in driver_standings if int(s.get("wins","0")) > 0]
        win_vals   = [int(s.get("wins", 0)) for s in driver_standings if int(s.get("wins","0")) > 0]
        win_colors = [
            get_team_color(
                s.get("Constructors", [{}])[0].get("constructorId", "")
                if s.get("Constructors") else ""
            )
            for s in driver_standings if int(s.get("wins","0")) > 0
        ]

        if win_names:
            fig3 = go.Figure(go.Bar(
                x=win_names, y=win_vals,
                marker=dict(color=win_colors),
                hovertemplate="%{x}: %{y} wins<extra></extra>",
            ))
            layout3 = make_plotly_layout(f"{season} Race Wins", height=300)
            layout3["yaxis"]["title"] = "Wins"
            fig3.update_layout(**layout3)
            st.plotly_chart(fig3, width='stretch')
        else:
            st.info("No wins data available yet.")
