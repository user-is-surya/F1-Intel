"""
F1Intel — Driver Intelligence Center
"""

import streamlit as st
st.set_page_config(page_title="Drivers — F1Intel", page_icon="👤", layout="wide")

import plotly.graph_objects as go
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.driver_card import render_driver_profile, render_driver_mini
from components.standings_table import render_race_results_table
from components.kpi_cards import render_kpi_row
from services.jolpica_service import (
    get_latest_standings, get_latest_constructor_standings,
    get_drivers, get_driver_standings, get_driver_info,
    get_driver_season_results, get_driver_career_stats,
)
from utils.flags import get_flag, get_country_flag
from utils.formatters import format_date, format_laptime
from config.settings import CURRENT_SEASON
from utils.colors import hex_alpha as _hex_alpha
from config.teams import get_team_color

load_css()
season = render_sidebar() or CURRENT_SEASON
page_header("Driver Intelligence Center", "Profiles, statistics & head-to-head analysis", "👤")

drivers_list     = get_drivers(season)
driver_standings = get_driver_standings(season)

standings_map = {s.get("Driver",{}).get("driverId",""): s for s in driver_standings}
driver_id_map = {
    f"{d.get('givenName','')} {d.get('familyName','')}": d.get("driverId","")
    for d in drivers_list
}
driver_names = sorted(driver_id_map.keys())

if not driver_names:
    st.markdown('<div class="glass-card" style="padding:2rem;text-align:center;color:var(--text-secondary);">No driver data available for this season.</div>', unsafe_allow_html=True)
    st.stop()

tab1, tab2, tab3 = st.tabs(["👤 Driver Profile","⚔️ Head-to-Head","📋 All Drivers"])

# ── Tab 1: Profile ──────────────────────────────────────────────────────────
with tab1:
    # Respect ?driver=<driverId> in the URL — lets other pages link straight
    # to a specific driver's profile (e.g. clicking a name in standings).
    id_to_name = {v: k for k, v in driver_id_map.items()}
    default_idx = 0
    requested_id = st.query_params.get("driver")
    if requested_id and requested_id in id_to_name:
        requested_name = id_to_name[requested_id]
        if requested_name in driver_names:
            default_idx = driver_names.index(requested_name)

    col_sel, _ = st.columns([1,2])
    with col_sel:
        sel_name = st.selectbox("Driver", driver_names, index=default_idx, key="drv_sel")

    # Keep the URL in sync so the selection is shareable/bookmarkable, and so
    # re-clicking the same driver elsewhere doesn't reset the selectbox.
    sel_id_for_url = driver_id_map.get(sel_name, "")
    if sel_id_for_url and st.query_params.get("driver") != sel_id_for_url:
        st.query_params["driver"] = sel_id_for_url

    sel_id = driver_id_map.get(sel_name,"")
    if not sel_id:
        st.stop()

    with st.spinner(f"Loading {sel_name}…"):
        d_info   = get_driver_info(sel_id) or {}
        standing = standings_map.get(sel_id)
        s_results= get_driver_season_results(sel_id, season)
        career   = get_driver_career_stats(sel_id)

    render_driver_profile(d_info, standing, career)
    divider()

    section_header("Statistics")
    wins_c  = career.get("wins",0)
    poles_c = career.get("poles",0)
    s_wins  = sum(1 for r in s_results if r.get("Results") and r["Results"][0].get("position")=="1")
    s_pods  = sum(1 for r in s_results if r.get("Results") and int(r["Results"][0].get("position",99))<=3)
    s_pts   = standing.get("points","0") if standing else "0"
    s_pos   = standing.get("position","—") if standing else "—"

    render_kpi_row([
        {"value":str(wins_c),  "label":"Career Wins",      "icon":"🏆","color":"#FFD700"},
        {"value":str(poles_c), "label":"Career Poles",     "icon":"⚡","color":"#9C27B0"},
        {"value":str(s_wins),  "label":f"{season} Wins",   "icon":"🥇","color":"#E10600"},
        {"value":str(s_pods),  "label":f"{season} Podiums","icon":"🥈","color":"#C0C0C0"},
        {"value":str(s_pts),   "label":f"{season} Points", "icon":"💯","color":"#00D2BE"},
        {"value":str(s_pos),   "label":"Championship",     "icon":"📊","color":"#FFFFFF"},
    ], cols=6)

    if s_results:
        divider()
        section_header(f"{season} Season")

        team_color = "#E10600"
        if standing and standing.get("Constructors"):
            team_color = get_team_color(standing["Constructors"][0].get("constructorId",""))

        r_names, pts_list, pos_list = [], [], []
        for r in s_results:
            res = r.get("Results",[{}])
            if not res:
                continue
            rn = r.get("raceName","").replace(" Grand Prix","")
            rp = res[0].get("position","—")
            rpts = float(res[0].get("points",0))
            r_names.append(rn)
            pts_list.append(rpts)
            try:
                pos_list.append(int(rp))
            except Exception:
                pos_list.append(None)

        if r_names:
            c1, c2 = st.columns(2)
            with c1:
                fig1 = go.Figure(go.Bar(x=r_names,y=pts_list,marker_color=team_color,
                    hovertemplate="%{x}<br>Pts: %{y}<extra></extra>"))
                l1 = make_plotly_layout(f"{season} Points per Race",height=280)
                l1["xaxis"]["tickangle"]=-30; l1["yaxis"]["title"]="Points"
                fig1.update_layout(**l1)
                st.plotly_chart(fig1,width='stretch')
            with c2:
                pc = [p if p else 20 for p in pos_list]
                fig2 = go.Figure(go.Scatter(x=r_names,y=pc,mode="lines+markers",
                    line=dict(color=team_color,width=2),marker=dict(size=6),
                    hovertemplate="%{x}<br>P%{y}<extra></extra>"))
                l2 = make_plotly_layout(f"{season} Finishing Positions",height=280)
                l2["xaxis"]["tickangle"]=-30; l2["yaxis"]["title"]="Position"
                l2["yaxis"]["autorange"]="reversed"; l2["yaxis"]["dtick"]=1
                fig2.update_layout(**l2)
                st.plotly_chart(fig2,width='stretch')

        divider()
        section_header("Race-by-Race Results")
        season_results_rows = []
        for r in s_results:
            res = r.get("Results",[{}])
            if not res:
                continue
            rn   = r.get("raceName","")
            rd   = r.get("date","")
            rv   = res[0]
            rpos = rv.get("position","—")
            rgrd = rv.get("grid","—")
            rpts = rv.get("points","0")
            rst  = rv.get("status","—")
            rt   = rv.get("Time",{}).get("time",rst) if rv.get("Time") else rst
            rfl  = rv.get("FastestLap",{}).get("Time",{}).get("time","") if rv.get("FastestLap") else ""
            fl_r = rv.get("FastestLap",{}).get("rank","") if rv.get("FastestLap") else ""
            time_display = f"{rt} ⚡{rfl}" if fl_r == "1" and rfl else rt
            season_results_rows.append({
                "Date": format_date(rd), "Race": rn, "Pos": rpos,
                "Grid": rgrd, "Time": time_display, "Pts": rpts,
            })

        if season_results_rows:
            import pandas as pd
            df_season = pd.DataFrame(season_results_rows)
            st.dataframe(df_season, hide_index=True, width='stretch')

        divider()
        section_header("Performance Radar")
        if standing:
            total_r = len(s_results) or 1
            avg_pts = sum(float(r["Results"][0].get("points",0)) for r in s_results if r.get("Results")) / total_r
            vals = [
                min(avg_pts/18,1)*10,
                min(s_wins/total_r*100/30,1)*10,
                min(s_pods/total_r*100/60,1)*10,
                min(float(s_pts)/500,1)*10,
                min(wins_c/100,1)*10,
            ]
            cats = ["Points Rate","Win Rate","Podium Rate","Season Points","Career Wins"]
            fig_r = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill="toself", fillcolor=_hex_alpha(team_color, "33"),
                line=dict(color=team_color,width=2),
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True,range=[0,10],
                        gridcolor="rgba(128,128,128,0.18)",tickfont=dict(color="rgba(128,128,128,0.72)",size=8)),
                    angularaxis=dict(gridcolor="rgba(128,128,128,0.18)",tickfont=dict(color="rgba(128,128,128,0.9)")),
                    bgcolor="rgba(0,0,0,0)"),
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                height=360, margin=dict(l=60,r=60,t=30,b=30), showlegend=False,
            )
            st.plotly_chart(fig_r, width='stretch')
    else:
        st.markdown(f'<div class="glass-card" style="padding:1.2rem;text-align:center;color:var(--text-muted);">No race results found for {sel_name} in {season}.</div>', unsafe_allow_html=True)

# ── Tab 2: Head-to-Head ─────────────────────────────────────────────────────
with tab2:
    section_header("Head-to-Head Comparison")
    c1, c2 = st.columns(2)
    with c1:
        d1_name = st.selectbox("Driver 1", driver_names, index=0, key="h2h1")
    with c2:
        d2_name = st.selectbox("Driver 2", driver_names, index=min(1,len(driver_names)-1), key="h2h2")

    d1_id = driver_id_map.get(d1_name,"")
    d2_id = driver_id_map.get(d2_name,"")

    if d1_id == d2_id:
        st.markdown('<div class="glass-card" style="padding:0.8rem;text-align:center;color:var(--text-secondary);">Select two different drivers.</div>', unsafe_allow_html=True)
    elif d1_id and d2_id:
        with st.spinner("Loading comparison…"):
            res1 = get_driver_season_results(d1_id, season)
            res2 = get_driver_season_results(d2_id, season)
            std1 = standings_map.get(d1_id,{})
            std2 = standings_map.get(d2_id,{})
            cs1  = get_driver_career_stats(d1_id)
            cs2  = get_driver_career_stats(d2_id)

        def get_color(std):
            if std and std.get("Constructors"):
                return get_team_color(std["Constructors"][0].get("constructorId",""))
            return "#E10600"

        c1c = get_color(std1); c2c = get_color(std2)

        def metrics(results, standing, career):
            wins = sum(1 for r in results if r.get("Results") and r["Results"][0].get("position")=="1")
            pods = sum(1 for r in results if r.get("Results") and int(r["Results"][0].get("position",99))<=3)
            pts  = float(standing.get("points",0)) if standing else 0
            pos  = int(standing.get("position",99)) if standing else 99
            n    = len(results) or 1
            fl   = sum(1 for r in results if r.get("Results") and r["Results"][0].get("FastestLap",{}).get("rank")=="1")
            return dict(wins=wins,podiums=pods,points=pts,position=pos,races=n,
                        career_wins=career.get("wins",0),career_poles=career.get("poles",0),fl=fl)

        m1 = metrics(res1,std1,cs1)
        m2 = metrics(res2,std2,cs2)

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:center;margin-bottom:1rem;">
            <div class="glass-card" style="text-align:center;border-top:3px solid {c1c};">
                <div style="font-size:1.3rem;font-weight:800;color:{c1c};">{d1_name}</div>
                <div style="font-size:0.78rem;color:var(--text-muted);">P{m1['position']} · {m1['points']:.0f} pts</div>
            </div>
            <div style="text-align:center;font-size:1.1rem;font-weight:900;color:var(--text-faint);">VS</div>
            <div class="glass-card" style="text-align:center;border-top:3px solid {c2c};">
                <div style="font-size:1.3rem;font-weight:800;color:{c2c};">{d2_name}</div>
                <div style="font-size:0.78rem;color:var(--text-muted);">P{m2['position']} · {m2['points']:.0f} pts</div>
            </div>
        </div>""", unsafe_allow_html=True)

        cats   = ["Points","Wins","Podiums","Fastest Laps","Career Wins","Career Poles"]
        vals1  = [m1["points"],m1["wins"],m1["podiums"],m1["fl"],m1["career_wins"],m1["career_poles"]]
        vals2  = [m2["points"],m2["wins"],m2["podiums"],m2["fl"],m2["career_wins"],m2["career_poles"]]
        fig_h  = go.Figure()
        fig_h.add_trace(go.Bar(name=d1_name,x=cats,y=vals1,marker_color=c1c))
        fig_h.add_trace(go.Bar(name=d2_name,x=cats,y=vals2,marker_color=c2c))
        lh = make_plotly_layout(f"{d1_name} vs {d2_name}",height=360)
        lh["barmode"]="group"
        fig_h.update_layout(**lh)
        st.plotly_chart(fig_h, width='stretch')

# ── Tab 3: All Drivers ──────────────────────────────────────────────────────
with tab3:
    section_header(f"{season} Driver Grid")
    if drivers_list:
        cols = st.columns(3)
        for i, d in enumerate(drivers_list):
            with cols[i%3]:
                render_driver_mini(d, standings_map.get(d.get("driverId","")))
    else:
        st.markdown('<div class="glass-card" style="padding:1.5rem;text-align:center;color:var(--text-muted);">No driver data available.</div>', unsafe_allow_html=True)
