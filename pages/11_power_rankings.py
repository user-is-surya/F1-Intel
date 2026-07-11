"""
F1Intel — Power Rankings & Advanced Analytics
Driver form, momentum, qualifying specialists, consistency index & more.
"""

import streamlit as st
st.set_page_config(page_title="Power Rankings — F1Intel", page_icon="⭐", layout="wide")

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from collections import defaultdict
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from services.jolpica_service import (
    get_latest_standings, get_latest_constructor_standings,
    get_driver_standings, get_constructor_standings,
    get_schedule, get_race_results, get_qualifying_results,
    get_pit_stops, get_drivers
)
from utils.flags import get_flag, get_country_flag
from utils.formatters import format_points
from config.settings import CURRENT_SEASON
from html import escape as _esc
from utils.colors import hex_alpha as _hex_alpha
from config.teams import get_team_color

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Power Rankings", "Form index, momentum, consistency & advanced analytics", "⭐")

# ── Load season data ──────────────────────────────────────────────────────────
with st.spinner("Loading season analytics…"):
    driver_standings = get_driver_standings(season)
    constructor_standings = get_constructor_standings(season)
    schedule = get_schedule(season)

if not driver_standings or not schedule:
    st.info("Insufficient data for power rankings. Check that the season has races.")
    st.stop()

# ── Build race-by-race data ────────────────────────────────────────────────────
from datetime import datetime
import pytz
now = datetime.now(pytz.UTC)

completed_races = []
for race in schedule:
    try:
        rd = datetime.fromisoformat(
            race.get("date","2099-01-01") + "T" +
            race.get("time","12:00:00Z").rstrip("Z") + "+00:00"
        )
        if rd < now:
            completed_races.append(race)
    except Exception:
        pass

@st.cache_data(ttl=600, show_spinner=False)
def build_season_data(season: int, completed: list) -> dict:
    """Build comprehensive per-driver per-race dataset."""
    race_data   = {}  # {round_num: {driver_id: {pos, pts, grid, status, q_pos}}}
    driver_ids  = set()

    for race in completed:
        rnd       = race.get("round","")
        r_results = get_race_results(season, rnd)
        q_results = get_qualifying_results(season, rnd)

        q_map = {
            r.get("Driver",{}).get("driverId",""): int(r.get("position",99))
            for r in q_results
        }

        race_data[rnd] = {}
        for r in r_results:
            did  = r.get("Driver",{}).get("driverId","")
            if not did:
                continue
            driver_ids.add(did)
            try:
                pos = int(r.get("position", 20))
            except Exception:
                pos = 20
            try:
                grid = int(r.get("grid", 20))
            except Exception:
                grid = 20
            pts    = float(r.get("points", 0))
            status = r.get("status","")
            fl     = r.get("FastestLap",{}).get("rank","") if r.get("FastestLap") else ""

            race_data[rnd][did] = {
                "position": pos,
                "grid":     grid,
                "points":   pts,
                "status":   status,
                "q_pos":    q_map.get(did, 20),
                "fastest_lap": fl == "1",
                "dnf":      status.lower() not in ("finished",) and not status.startswith("+"),
            }

    return {"race_data": race_data, "driver_ids": list(driver_ids)}

with st.spinner("Crunching statistics…"):
    season_data   = build_season_data(season, completed_races)
    race_data     = season_data["race_data"]
    all_driver_ids = season_data["driver_ids"]

# Build driver name map
driver_name_map = {
    s.get("Driver",{}).get("driverId",""): {
        "name": f"{s.get('Driver',{}).get('givenName','')} {s.get('Driver',{}).get('familyName','')}",
        "family": s.get("Driver",{}).get("familyName",""),
        "nat":    s.get("Driver",{}).get("nationality",""),
        "cid":    s.get("Constructors",[{}])[0].get("constructorId","") if s.get("Constructors") else "",
        "team":   s.get("Constructors",[{}])[0].get("name","") if s.get("Constructors") else "",
        "points": float(s.get("points",0)),
        "position": int(s.get("position",99)),
    }
    for s in driver_standings
}

# Compute per-driver aggregates
def compute_driver_stats(driver_id: str, race_data: dict) -> dict:
    positions    = []
    grid_pos     = []
    points_list  = []
    q_positions  = []
    dnf_count    = 0
    fl_count     = 0
    overtakes    = []

    for rnd, drivers in race_data.items():
        if driver_id not in drivers:
            continue
        d = drivers[driver_id]
        positions.append(d["position"])
        grid_pos.append(d["grid"])
        points_list.append(d["points"])
        q_positions.append(d["q_pos"])
        if d["dnf"]:       dnf_count += 1
        if d["fastest_lap"]: fl_count  += 1
        overtakes.append(d["grid"] - d["position"])  # positive = gained positions

    if not positions:
        return {}

    n = len(positions)
    avg_pos       = np.mean(positions)
    avg_grid      = np.mean(grid_pos)
    avg_pts       = np.mean(points_list)
    avg_q         = np.mean(q_positions)
    consistency   = 100 - (np.std(positions) / 10 * 100)   # 0–100, higher = consistent
    consistency   = max(0, min(100, consistency))
    total_pts     = sum(points_list)
    podiums       = sum(1 for p in positions if p <= 3)
    wins          = sum(1 for p in positions if p == 1)
    top10         = sum(1 for p in positions if p <= 10)
    q_vs_race     = avg_grid - avg_pos  # positive = gains positions in race
    overtakes_avg = np.mean(overtakes) if overtakes else 0

    # Recent form: last 4 races weighted
    recent_n   = min(4, n)
    recent_pos = positions[-recent_n:]
    recent_pts = points_list[-recent_n:]
    form_score = np.mean([(21 - p) for p in recent_pos]) * 5  # 0–100

    # Power rating composite
    power = (
        (100 - avg_pos * 4.5) * 0.25 +
        form_score * 0.30 +
        consistency * 0.20 +
        min(avg_pts / 18 * 100, 100) * 0.15 +
        min(q_vs_race * 5 + 50, 100) * 0.10
    )
    power = max(0, min(100, power))

    return {
        "n_races":      n,
        "avg_pos":      avg_pos,
        "avg_grid":     avg_grid,
        "avg_pts":      avg_pts,
        "avg_q":        avg_q,
        "consistency":  consistency,
        "total_pts":    total_pts,
        "podiums":      podiums,
        "wins":         wins,
        "top10":        top10,
        "dnf_count":    dnf_count,
        "fl_count":     fl_count,
        "form_score":   form_score,
        "power":        power,
        "q_vs_race":    q_vs_race,
        "overtakes_avg": overtakes_avg,
    }

# Compute stats for all drivers
all_stats = {}
for did in all_driver_ids:
    if did in driver_name_map:
        stats = compute_driver_stats(did, race_data)
        if stats:
            all_stats[did] = stats

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⭐ Power Rankings", "📈 Form & Momentum",
    "🎯 Consistency Index", "🏎 Qualifying Specialists",
    "💨 Race Pace", "🔢 Full Analytics Table"
])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Power Rankings
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section_header(f"{season} F1Intel Power Rankings")
    st.caption("Composite rating based on position, points, form, consistency & qualifying performance.")

    ranked = sorted(all_stats.items(), key=lambda x: x[1]["power"], reverse=True)

    if not ranked:
        st.info("Not enough race data to compute rankings yet.")
    else:
        for rank, (did, stats) in enumerate(ranked, start=1):
            info       = driver_name_map.get(did, {})
            name       = info.get("name","")
            flag       = get_flag(info.get("nat",""))
            team       = info.get("team","")
            cid        = info.get("cid","")
            tc         = get_team_color(cid)
            power      = stats["power"]
            form       = stats["form_score"]
            consist    = stats["consistency"]
            pts        = stats["total_pts"]
            wins       = stats["wins"]
            podiums    = stats["podiums"]

            # Bar width
            bar_pct = f"{power:.0f}%"
            rank_color = "#FFD700" if rank == 1 else ("#C0C0C0" if rank == 2 else ("#CD7F32" if rank == 3 else tc))
            trend_arrow = "▲" if form > 60 else ("▼" if form < 40 else "→")
            trend_color = "#4CAF50" if form > 60 else ("#E10600" if form < 40 else "#FFD700")

            st.markdown(f"""
            <div class="glass-card" style="padding:0.9rem 1.2rem;margin-bottom:0.5rem;
                         border-left:3px solid {rank_color};">
                <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
                    <div style="font-size:1.5rem;font-weight:900;color:{rank_color};
                                min-width:36px;text-align:center;">
                        {rank}
                    </div>
                    <div style="flex:1;min-width:150px;">
                        <div style="font-weight:700;font-size:1rem;">
                            {flag} {name}
                        </div>
                        <div style="font-size:0.75rem;color:var(--text-secondary);">
                            {team}
                        </div>
                    </div>
                    <div style="flex:2;min-width:120px;">
                        <div style="display:flex;align-items:center;gap:0.5rem;">
                            <div style="flex:1;height:8px;background:var(--overlay-soft);
                                        border-radius:4px;overflow:hidden;">
                                <div style="width:{bar_pct};height:100%;
                                            background:linear-gradient(90deg,{tc},{rank_color});
                                            border-radius:4px;transition:width 0.5s;"></div>
                            </div>
                            <div style="font-size:1rem;font-weight:800;color:{rank_color};
                                        min-width:42px;text-align:right;">
                                {power:.0f}
                            </div>
                        </div>
                        <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;
                                    color:var(--text-muted);margin-top:2px;">Power Rating</div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(5,50px);
                                gap:0.3rem;text-align:center;">
                        <div>
                            <div style="font-weight:700;font-size:0.88rem;">{pts:.0f}</div>
                            <div style="font-size:0.6rem;color:var(--text-muted);">PTS</div>
                        </div>
                        <div>
                            <div style="font-weight:700;font-size:0.88rem;">{wins}</div>
                            <div style="font-size:0.6rem;color:var(--text-muted);">WINS</div>
                        </div>
                        <div>
                            <div style="font-weight:700;font-size:0.88rem;">{podiums}</div>
                            <div style="font-size:0.6rem;color:var(--text-muted);">PODS</div>
                        </div>
                        <div>
                            <div style="font-weight:700;font-size:0.88rem;color:{trend_color};">
                                {trend_arrow}
                            </div>
                            <div style="font-size:0.6rem;color:var(--text-muted);">FORM</div>
                        </div>
                        <div>
                            <div style="font-weight:700;font-size:0.88rem;color:#00D2BE;">
                                {consist:.0f}
                            </div>
                            <div style="font-size:0.6rem;color:var(--text-muted);">CONS</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Radar comparison of top 3
    if len(ranked) >= 3:
        divider()
        section_header("Top 3 Radar Comparison")
        top3    = ranked[:3]
        metrics = ["Power", "Form", "Consistency", "Avg Points", "Qualifying"]
        fig_r   = go.Figure()
        colors  = ["#FFD700", "#C0C0C0", "#CD7F32"]

        for (did, stats), color in zip(top3, colors):
            info = driver_name_map.get(did, {})
            name = info.get("family","")
            vals = [
                stats["power"],
                stats["form_score"],
                stats["consistency"],
                min(stats["avg_pts"] / 18 * 100, 100),
                max(0, 100 - (stats["avg_q"] - 1) * 5),
            ]
            fig_r.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=metrics + [metrics[0]],
                fill="toself",
                fillcolor=_hex_alpha(color, "22"),
                line=dict(color=color, width=2),
                name=name,
            ))

        fig_r.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,100],
                                gridcolor="rgba(128,128,128,0.18)",
                                tickfont=dict(size=8, color="rgba(128,128,128,0.72)")),
                angularaxis=dict(gridcolor="rgba(128,128,128,0.18)",
                                 tickfont=dict(color="rgba(128,128,128,0.9)")),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=420,
            margin=dict(l=60,r=60,t=30,b=40),
        )
        st.plotly_chart(fig_r, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Form & Momentum
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section_header("Driver Form — Last 4 Races")
    st.caption("Form score based on recent finishing positions. Higher = better current form.")

    form_ranked = sorted(all_stats.items(), key=lambda x: x[1]["form_score"], reverse=True)

    if form_ranked:
        names_form = [driver_name_map.get(d,{}).get("family","") for d,_ in form_ranked]
        vals_form  = [s["form_score"] for _,s in form_ranked]
        colors_form = [
            get_team_color(driver_name_map.get(d,{}).get("cid",""))
            for d,_ in form_ranked
        ]

        fig_form = go.Figure(go.Bar(
            x=names_form, y=vals_form,
            marker=dict(color=colors_form, line=dict(color="rgba(0,0,0,0.3)",width=1)),
            hovertemplate="%{x}: Form Score %{y:.1f}<extra></extra>",
        ))
        lf = make_plotly_layout("Driver Form Score (Last 4 Races)", height=360)
        lf["xaxis"]["tickangle"] = -30
        lf["yaxis"]["title"]     = "Form Score (0–100)"
        lf["yaxis"]["range"]     = [0, 105]
        fig_form.update_layout(**lf)
        st.plotly_chart(fig_form, width='stretch')

    divider()
    section_header("Points Momentum — Race-by-Race")

    # Per-driver rolling points
    sorted_rounds = sorted(race_data.keys(), key=lambda x: int(x))
    col_drv, _ = st.columns([1,2])
    with col_drv:
        momentum_drivers = st.multiselect(
            "Drivers", list(driver_name_map.keys()),
            format_func=lambda d: driver_name_map.get(d,{}).get("family",""),
            default=list(driver_name_map.keys())[:5],
            key="momentum_drvs"
        )

    if momentum_drivers:
        fig_mom = go.Figure()
        for did in momentum_drivers:
            info   = driver_name_map.get(did,{})
            name   = info.get("family","")
            tc     = get_team_color(info.get("cid",""))
            pts_seq = []
            cumulative = 0.0
            for rnd in sorted_rounds:
                if did in race_data.get(rnd,{}):
                    cumulative += race_data[rnd][did]["points"]
                pts_seq.append(cumulative)

            fig_mom.add_trace(go.Scatter(
                x=list(range(1, len(sorted_rounds)+1)),
                y=pts_seq,
                name=name,
                mode="lines+markers",
                line=dict(color=tc, width=2),
                marker=dict(size=5),
            ))

        lm = make_plotly_layout("Cumulative Points Progression", height=400)
        lm["xaxis"]["title"] = "Race Number"
        lm["yaxis"]["title"] = "Cumulative Points"
        fig_mom.update_layout(**lm)
        st.plotly_chart(fig_mom, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Consistency Index
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section_header("Driver Consistency Index")
    st.caption("Based on standard deviation of finishing positions. 100 = perfectly consistent, 0 = highly variable.")

    consist_ranked = sorted(all_stats.items(), key=lambda x: x[1]["consistency"], reverse=True)

    for rank, (did, stats) in enumerate(consist_ranked, start=1):
        info    = driver_name_map.get(did,{})
        name    = info.get("name","")
        flag    = get_flag(info.get("nat",""))
        team    = info.get("team","")
        cid_c   = info.get("cid","")
        tc      = get_team_color(cid_c)
        c_score = stats["consistency"]
        dnfs    = stats["dnf_count"]
        avg_p   = stats["avg_pos"]
        n_races = stats["n_races"]

        bar_pct = f"{c_score:.0f}%"
        color   = "#4CAF50" if c_score >= 70 else ("#FFD700" if c_score >= 50 else "#E10600")

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;padding:0.5rem 0;
                    border-bottom:1px solid var(--divider-soft);">
            <div style="min-width:24px;text-align:center;font-weight:700;
                        color:var(--text-muted);">{rank}</div>
            <div style="min-width:180px;">
                <div style="font-weight:600;">{flag} {name}</div>
                <div style="font-size:0.72rem;color:var(--text-muted);">{team}</div>
            </div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <div style="flex:1;height:6px;background:var(--overlay-soft);
                                border-radius:3px;overflow:hidden;">
                        <div style="width:{bar_pct};height:100%;background:{color};
                                    border-radius:3px;"></div>
                    </div>
                    <div style="font-weight:800;font-size:0.95rem;color:{color};min-width:36px;">
                        {c_score:.0f}
                    </div>
                </div>
            </div>
            <div style="display:flex;gap:1.5rem;text-align:center;">
                <div>
                    <div style="font-size:0.85rem;font-weight:700;">{avg_p:.1f}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);">AVG POS</div>
                </div>
                <div>
                    <div style="font-size:0.85rem;font-weight:700;
                                color:{'#E10600' if dnfs > 2 else 'var(--text-primary)'};">{dnfs}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);">DNFs</div>
                </div>
                <div>
                    <div style="font-size:0.85rem;font-weight:700;">{n_races}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);">RACES</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Qualifying Specialists
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    section_header("Qualifying Specialists Ranking")
    st.caption("Ranked by average qualifying position. Lower = better qualifier.")

    qual_ranked = sorted(
        [(d, s) for d, s in all_stats.items() if s["avg_q"] < 20],
        key=lambda x: x[1]["avg_q"]
    )

    if qual_ranked:
        names_q = [driver_name_map.get(d,{}).get("family","") for d,_ in qual_ranked]
        avg_q   = [s["avg_q"] for _,s in qual_ranked]
        avg_r   = [s["avg_pos"] for _,s in qual_ranked]
        colors_q = [get_team_color(driver_name_map.get(d,{}).get("cid","")) for d,_ in qual_ranked]

        fig_q = go.Figure()
        fig_q.add_trace(go.Bar(
            name="Avg Qualifying", x=names_q, y=avg_q,
            marker_color=colors_q,
            hovertemplate="%{x}<br>Avg Q: P%{y:.1f}<extra></extra>",
        ))
        fig_q.add_trace(go.Scatter(
            name="Avg Race", x=names_q, y=avg_r,
            mode="markers",
            marker=dict(color="white", size=8, symbol="diamond",
                        line=dict(color="rgba(0,0,0,0.4)", width=1)),
            hovertemplate="%{x}<br>Avg Race: P%{y:.1f}<extra></extra>",
        ))
        lq = make_plotly_layout("Qualifying vs Race Performance", height=380)
        lq["xaxis"]["tickangle"] = -30
        lq["yaxis"]["title"]     = "Average Position"
        lq["yaxis"]["autorange"] = "reversed"
        lq["yaxis"]["range"]     = [22, 0]
        lq["barmode"]            = "overlay"
        fig_q.update_layout(**lq)
        st.plotly_chart(fig_q, width='stretch')

        divider()
        section_header("Qualifying → Race Delta")
        st.caption("Positive = gains positions in the race vs grid. Negative = loses positions.")

        for did, stats in qual_ranked:
            info  = driver_name_map.get(did,{})
            name  = info.get("name","")
            flag  = get_flag(info.get("nat",""))
            tc    = get_team_color(info.get("cid",""))
            delta = stats["q_vs_race"]
            color = "#4CAF50" if delta > 0.5 else ("#E10600" if delta < -0.5 else "#FFD700")
            sign  = "+" if delta >= 0 else ""
            bar_w = min(abs(delta) / 5 * 100, 100)
            bar_dir = "left:50%;" if delta >= 0 else f"right:50%;"

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;padding:0.4rem 0;
                        border-bottom:1px solid var(--divider-soft);">
                <div style="min-width:180px;">
                    <span style="font-weight:600;">{flag} {name}</span>
                </div>
                <div style="flex:1;position:relative;height:8px;
                            background:var(--overlay-soft);border-radius:4px;overflow:hidden;">
                    <div style="position:absolute;top:0;bottom:0;{bar_dir}
                                width:{bar_w}%;background:{color};border-radius:4px;"></div>
                    <div style="position:absolute;top:0;bottom:0;left:50%;
                                width:1px;background:var(--overlay-soft);"></div>
                </div>
                <div style="font-weight:800;font-size:0.95rem;color:{color};min-width:52px;text-align:right;">
                    {sign}{delta:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 5 — Race Pace
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    section_header("Race Pace Rankings")
    st.caption("Based on average finishing position and points per race. Lower average position = stronger race pace.")

    pace_ranked = sorted(
        [(d, s) for d, s in all_stats.items() if s["n_races"] > 0],
        key=lambda x: x[1]["avg_pos"]
    )

    # Scatter: avg qualifying vs avg race position
    fig_pace = go.Figure()
    for did, stats in pace_ranked:
        info   = driver_name_map.get(did,{})
        name   = info.get("family","")
        cid_p  = info.get("cid","")
        tc     = get_team_color(cid_p)
        fig_pace.add_trace(go.Scatter(
            x=[stats["avg_q"]],
            y=[stats["avg_pos"]],
            mode="markers+text",
            marker=dict(color=tc, size=14, line=dict(color="white",width=1.5)),
            text=[name],
            textposition="top center",
            textfont=dict(size=9, color="rgba(128,128,128,0.9)"),
            name=name,
            showlegend=False,
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Avg Q: P%{x:.1f}<br>Avg Race: P%{y:.1f}<extra></extra>"
            ),
        ))

    # Diagonal reference line
    min_v = 1
    max_v = 20
    fig_pace.add_trace(go.Scatter(
        x=[min_v, max_v], y=[min_v, max_v],
        mode="lines",
        line=dict(color="rgba(128,128,128,0.27)", dash="dash", width=1),
        showlegend=False, hoverinfo="skip",
        name="Equal Q & Race",
    ))

    lp = make_plotly_layout("Race vs Qualifying Performance", height=480)
    lp["xaxis"]["title"]    = "Avg Qualifying Position"
    lp["yaxis"]["title"]    = "Avg Race Position"
    lp["xaxis"]["autorange"] = "reversed"
    lp["yaxis"]["autorange"] = "reversed"
    lp["xaxis"]["range"]    = [22, 0]
    lp["yaxis"]["range"]    = [22, 0]
    fig_pace.update_layout(**lp)
    st.caption("Top-left = strong in both. Below diagonal = gains positions in races. Above = loses positions.")
    st.plotly_chart(fig_pace, width='stretch')

    divider()
    section_header("Fastest Lap Leaders")
    fl_ranked = sorted(
        [(d, s) for d, s in all_stats.items()],
        key=lambda x: x[1]["fl_count"],
        reverse=True
    )

    # Fastest lap data
    fl_data = [(did, stats["fl_count"]) for did, stats in all_stats.items() if stats.get("fl_count",0) > 0]
    fl_data_sorted = sorted(fl_data, key=lambda x: x[1], reverse=True)

    if fl_data_sorted:
        fl_names  = [driver_name_map.get(d,{}).get("family","") for d,_ in fl_data_sorted]
        fl_counts = [c for _,c in fl_data_sorted]
        fl_colors = [get_team_color(driver_name_map.get(d,{}).get("cid","")) for d,_ in fl_data_sorted]

        fig_fl = go.Figure(go.Bar(
            x=fl_names, y=fl_counts,
            marker=dict(color=fl_colors),
            hovertemplate="%{x}: %{y} fastest laps<extra></extra>",
        ))
        lfl = make_plotly_layout("Fastest Lap Count", height=300)
        lfl["yaxis"]["title"] = "Fastest Laps"
        lfl["yaxis"]["dtick"] = 1
        fig_fl.update_layout(**lfl)
        st.plotly_chart(fig_fl, width='stretch')
    else:
        st.info("No fastest lap data available yet.")


# ══════════════════════════════════════════════════════════════════════════════
# Tab 6 — Full Analytics Table
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    section_header("Complete Analytics Table")

    table_ranked = sorted(all_stats.items(), key=lambda x: x[1]["power"], reverse=True)
    analytics_rows = []

    for rank, (did, stats) in enumerate(table_ranked, start=1):
        info  = driver_name_map.get(did, {})
        name  = info.get("name", "")
        flag  = get_flag(info.get("nat", ""))
        team  = info.get("team", "")
        qvr   = stats["q_vs_race"]
        sign  = "+" if qvr >= 0 else ""

        analytics_rows.append({
            "#": rank,
            "Driver": f"{flag} {name}",
            "Team": team,
            "PWR": round(stats["power"]),
            "PTS": round(stats["total_pts"]),
            "W": stats["wins"],
            "POD": stats["podiums"],
            "T10": stats["top10"],
            "DNF": stats["dnf_count"],
            "FL": stats["fl_count"],
            "AvgR": round(stats["avg_pos"], 1),
            "AvgQ": round(stats["avg_q"], 1),
            "Q→R": f"{sign}{qvr:.1f}",
            "FORM": round(stats["form_score"]),
            "CONS": round(stats["consistency"]),
            "RCS": stats["n_races"],
        })

    if analytics_rows:
        import pandas as pd
        df_analytics = pd.DataFrame(analytics_rows)
        st.dataframe(
            df_analytics, hide_index=True, width='stretch',
            column_config={
                "#":   st.column_config.NumberColumn("#", width="small"),
                "PWR": st.column_config.NumberColumn("PWR", help="Composite power rating"),
                "DNF": st.column_config.NumberColumn("DNF", help="Did not finish"),
                "FL":  st.column_config.NumberColumn("FL", help="Fastest laps"),
                "AvgR":st.column_config.NumberColumn("AvgR", help="Average race position"),
                "AvgQ":st.column_config.NumberColumn("AvgQ", help="Average qualifying position"),
                "Q→R": st.column_config.TextColumn("Q→R", help="Positions gained vs grid"),
                "FORM":st.column_config.NumberColumn("FORM", help="Recent form score"),
                "CONS":st.column_config.NumberColumn("CONS", help="Consistency index"),
                "RCS": st.column_config.NumberColumn("RCS", help="Races completed"),
            },
        )
        st.caption(
            "PWR=Power Rating · W=Wins · POD=Podiums · T10=Top 10s · DNF=Did Not Finish · "
            "FL=Fastest Laps · AvgR=Avg Race Pos · AvgQ=Avg Quali Pos · Q→R=Positions Gained · "
            "FORM=Recent Form · CONS=Consistency · RCS=Races"
        )
    else:
        st.info("No analytics data available yet.")
