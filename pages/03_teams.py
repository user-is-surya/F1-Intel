"""
F1Intel — Team Intelligence Center
Constructor profiles, driver lineups, and team analytics.
"""

import streamlit as st
st.set_page_config(page_title="Teams — F1Intel", page_icon="🏎️", layout="wide")

import plotly.graph_objects as go
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.team_card import render_team_profile
from services.jolpica_service import (
    get_constructors, get_constructor_standings, get_drivers,
    get_constructor_season_results, get_driver_standings
)
from config.teams import get_team_color
from utils.flags import get_country_flag
from config.settings import CURRENT_SEASON

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Team Intelligence Center", "Constructor profiles, lineups & analytics", "🏎️")

# ── Load data ─────────────────────────────────────────────────────────────────
constructors_list     = get_constructors(season)
constructor_standings = get_constructor_standings(season)
drivers_list          = get_drivers(season)
driver_standings      = get_driver_standings(season)

standings_map = {
    s.get("Constructor", {}).get("constructorId", ""): s
    for s in constructor_standings
}

# Build driver-to-team map
driver_team_map: dict[str, list[dict]] = {}
for drv_std in driver_standings:
    constructors = drv_std.get("Constructors", [])
    if constructors:
        cid = constructors[0].get("constructorId", "")
        if cid not in driver_team_map:
            driver_team_map[cid] = []
        driver_team_map[cid].append(drv_std.get("Driver", {}))

constructor_name_map = {
    c.get("name", ""): c.get("constructorId", "")
    for c in constructors_list
}
con_names = sorted(constructor_name_map.keys())

tab1, tab2, tab3 = st.tabs(["🏗️ Team Profile", "⚔️ Team Comparison", "🏆 All Teams"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Team Profile
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_team_name = st.selectbox("Select Team", con_names, key="team_sel")

    cid      = constructor_name_map.get(selected_team_name, "")
    standing = standings_map.get(cid)
    constructor_info = next((c for c in constructors_list if c.get("constructorId") == cid), {})
    team_drivers     = driver_team_map.get(cid, [])
    team_color       = get_team_color(cid)

    render_team_profile(constructor_info, standing, team_drivers)

    divider()

    # ── Season results ────────────────────────────────────────────────────
    section_header(f"{season} Season Results")

    with st.spinner(f"Loading {selected_team_name} results…"):
        team_results = get_constructor_season_results(cid, season)

    if team_results:
        # Points per race chart
        race_names_short = []
        pts_race         = []
        best_pos_race    = []

        for race in team_results:
            r_name   = race.get("raceName", "").replace(" Grand Prix","")
            results  = race.get("Results", [])
            race_pts = sum(float(r.get("points", 0)) for r in results)
            best_pos = min((int(r.get("position", 99)) for r in results), default=99)
            race_names_short.append(r_name)
            pts_race.append(race_pts)
            best_pos_race.append(best_pos if best_pos < 99 else None)

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            fig1 = go.Figure(go.Bar(
                x=race_names_short, y=pts_race,
                marker_color=team_color,
                hovertemplate="%{x}<br>Points: %{y}<extra></extra>",
            ))
            l1 = make_plotly_layout(f"{selected_team_name} — Points per Race", height=300)
            l1["xaxis"]["tickangle"] = -30
            l1["yaxis"]["title"]     = "Points"
            fig1.update_layout(**l1)
            st.plotly_chart(fig1, width='stretch')

        with col_c2:
            pos_clean = [p if p else 20 for p in best_pos_race]
            fig2 = go.Figure(go.Scatter(
                x=race_names_short, y=pos_clean,
                mode="lines+markers",
                line=dict(color=team_color, width=2),
                marker=dict(size=7),
                hovertemplate="%{x}<br>Best Pos: P%{y}<extra></extra>",
            ))
            l2 = make_plotly_layout("Best Finish per Race", height=300)
            l2["xaxis"]["tickangle"] = -30
            l2["yaxis"]["title"]     = "Position"
            l2["yaxis"]["autorange"] = "reversed"
            l2["yaxis"]["dtick"]     = 1
            fig2.update_layout(**l2)
            st.plotly_chart(fig2, width='stretch')

        # Race results table — native dataframe (no HTML rendering risk)
        section_header("Race Results")
        table_rows = []
        for race in team_results:
            r_name  = race.get("raceName", "")
            r_date  = race.get("date", "")
            results = race.get("Results", [])
            for r in results:
                drv      = r.get("Driver", {})
                pos      = r.get("position", "—")
                pts      = r.get("points", "0")
                grid     = r.get("grid", "—")
                status   = r.get("status", "—")
                t        = r.get("Time", {}).get("time", status) if r.get("Time") else status
                drv_name = f"{drv.get('givenName','')} {drv.get('familyName','')}"
                table_rows.append({
                    "Date": r_date, "Race": r_name, "Driver": drv_name,
                    "Pos": pos, "Grid": grid, "Time": t, "Pts": pts,
                })

        if table_rows:
            import pandas as pd
            df = pd.DataFrame(table_rows)
            st.dataframe(
                df, hide_index=True, width='stretch',
                column_config={
                    "Pos": st.column_config.NumberColumn("Pos", width="small"),
                    "Grid": st.column_config.NumberColumn("Grid", width="small"),
                    "Pts": st.column_config.NumberColumn("Pts", width="small"),
                },
            )
        else:
            st.info("No race results found for this team.")
    else:
        st.info(f"No race results available for {selected_team_name} in {season}.")

    divider()
    section_header("Historical Championship Positions")

    with st.spinner("Loading championship history…"):
        history_years = []
        history_pos   = []
        history_pts   = []
        for yr in range(season, max(season-10, 2010)-1, -1):
            yr_standings = get_constructor_standings(yr)
            for s in yr_standings:
                if s.get("Constructor", {}).get("constructorId", "") == cid:
                    history_years.append(yr)
                    history_pos.append(int(s.get("position", 99)))
                    history_pts.append(float(s.get("points", 0)))
                    break

    if history_years:
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            fig_hp = go.Figure(go.Scatter(
                x=history_years, y=history_pos,
                mode="lines+markers",
                line=dict(color=team_color, width=2),
                marker=dict(size=8),
                hovertemplate="Year: %{x}<br>Position: P%{y}<extra></extra>",
            ))
            lh = make_plotly_layout(f"{selected_team_name} — Championship History", height=300)
            lh["yaxis"]["autorange"] = "reversed"
            lh["yaxis"]["dtick"]     = 1
            lh["yaxis"]["title"]     = "Championship Position"
            lh["xaxis"]["title"]     = "Season"
            fig_hp.update_layout(**lh)
            st.plotly_chart(fig_hp, width='stretch')

        with col_h2:
            fig_hpts = go.Figure(go.Bar(
                x=history_years, y=history_pts,
                marker_color=team_color,
                hovertemplate="Year: %{x}<br>Points: %{y}<extra></extra>",
            ))
            lhp = make_plotly_layout("Points per Season", height=300)
            lhp["yaxis"]["title"] = "Points"
            lhp["xaxis"]["title"] = "Season"
            fig_hpts.update_layout(**lhp)
            st.plotly_chart(fig_hpts, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Team Comparison
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section_header("Team vs Team Comparison")

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        team_a_name = st.selectbox("Team A", con_names, index=0, key="team_a")
    with c_col2:
        team_b_name = st.selectbox("Team B", con_names, index=min(1,len(con_names)-1), key="team_b")

    cid_a = constructor_name_map.get(team_a_name, "")
    cid_b = constructor_name_map.get(team_b_name, "")
    std_a = standings_map.get(cid_a, {})
    std_b = standings_map.get(cid_b, {})
    col_a = get_team_color(cid_a)
    col_b = get_team_color(cid_b)

    metrics_labels = ["Points", "Wins", "Position (inv)"]
    vals_a = [
        float(std_a.get("points", 0)),
        int(std_a.get("wins", 0)),
        max(0, 11 - int(std_a.get("position", 11))),
    ]
    vals_b = [
        float(std_b.get("points", 0)),
        int(std_b.get("wins", 0)),
        max(0, 11 - int(std_b.get("position", 11))),
    ]

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name=team_a_name, x=metrics_labels, y=vals_a,
                               marker_color=col_a))
    fig_comp.add_trace(go.Bar(name=team_b_name, x=metrics_labels, y=vals_b,
                               marker_color=col_b))
    lc = make_plotly_layout(f"{team_a_name} vs {team_b_name}", height=360)
    lc["barmode"] = "group"
    fig_comp.update_layout(**lc)
    st.plotly_chart(fig_comp, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — All Teams
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section_header(f"{season} Constructor Grid")

    if not constructors_list:
        st.info("No constructor data available.")
    else:
        cols = st.columns(2)
        for i, constructor in enumerate(constructors_list):
            cid_i    = constructor.get("constructorId", "")
            standing_i = standings_map.get(cid_i)
            drivers_i  = driver_team_map.get(cid_i, [])
            with cols[i % 2]:
                render_team_profile(constructor, standing_i, drivers_i)
