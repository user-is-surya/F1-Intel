"""
F1Intel — Home Dashboard
"""

import streamlit as st

st.set_page_config(
    page_title="F1Intel — Formula 1 Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.helpers import load_css, section_header, divider
from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_row, championship_leader_card, constructor_leader_card
from components.countdown import render_countdown, render_session_schedule
from components.standings_table import render_race_results_table, render_driver_standings, render_constructor_standings
from services.jolpica_service import (
    get_latest_standings, get_latest_constructor_standings,
    get_driver_standings, get_constructor_standings, get_schedule, get_last_race_results
)
from config.settings import CURRENT_SEASON
from utils.flags import get_country_flag
from utils.formatters import format_date
from datetime import datetime
import pytz

load_css()

season = render_sidebar() or CURRENT_SEASON

# ── Page title ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:1rem 0 0.4rem;">
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.16em;color:var(--text-muted);margin-bottom:0.3rem;">
        Formula 1 Intelligence Platform · {season}
    </div>
    <h1 style="font-size:2.6rem;font-weight:900;letter-spacing:-0.04em;margin:0;
               background:linear-gradient(135deg,var(--chrome-text-primary) 55%,var(--chrome-text-secondary));
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
        F1Intel Dashboard
    </h1>
    <div style="width:48px;height:3px;background:linear-gradient(90deg,#E10600,transparent);
                border-radius:2px;margin-top:0.7rem;"></div>
</div>
""", unsafe_allow_html=True)

divider()

# ── Load core data (one spinner, parallel-ish) ────────────────────────────────
with st.spinner("Loading season data…"):
    from concurrent.futures import ThreadPoolExecutor

    def _fetch_all():
        with ThreadPoolExecutor(max_workers=4) as ex:
            f_drv = ex.submit(get_latest_standings, season) if season == CURRENT_SEASON else ex.submit(get_driver_standings, season)
            f_con = ex.submit(get_latest_constructor_standings, season) if season == CURRENT_SEASON else ex.submit(get_constructor_standings, season)
            f_sch = ex.submit(get_schedule, season)
            f_res = ex.submit(get_last_race_results, season)
            return f_drv.result(), f_con.result(), f_sch.result(), f_res.result()

    driver_standings, constructor_standings, schedule, (last_race, results) = _fetch_all()

now = datetime.now(pytz.UTC)

def parse_dt(race):
    try:
        d = race.get("date","")
        t = race.get("time","12:00:00Z").rstrip("Z")
        return datetime.fromisoformat(f"{d}T{t}+00:00")
    except Exception:
        return None

past_races   = [r for r in schedule if (parse_dt(r) or now) < now]
future_races = [r for r in schedule if (parse_dt(r) or now) >= now]
next_race    = future_races[0] if future_races else None

# ── Championship Leaders ──────────────────────────────────────────────────────
section_header("Championship Leaders")
c1, c2 = st.columns(2)
with c1:
    if driver_standings:
        championship_leader_card(driver_standings[0])
    else:
        st.markdown("""
        <div class="glass-card" style="padding:1.5rem;text-align:center;">
            <div style="color:var(--text-muted);">Standings will appear once the season begins.</div>
        </div>""", unsafe_allow_html=True)
with c2:
    if constructor_standings:
        constructor_leader_card(constructor_standings[0])
    else:
        st.markdown("""
        <div class="glass-card" style="padding:1.5rem;text-align:center;">
            <div style="color:var(--text-muted);">Constructor standings not yet available.</div>
        </div>""", unsafe_allow_html=True)

divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_header("Season Overview")

total_races      = len(schedule)
completed_count  = len(past_races)
remaining_count  = len(future_races)

leader_family  = driver_standings[0].get("Driver",{}).get("familyName","—") if driver_standings else "—"
leader_pts     = driver_standings[0].get("points","0") if driver_standings else "0"
con_lead       = constructor_standings[0].get("Constructor",{}).get("name","—") if constructor_standings else "—"
con_pts        = constructor_standings[0].get("points","0") if constructor_standings else "0"

# Pole leader: driver with most points scored from pole (approximation: P1 grid positions in results)
# Fast KPI — just use wins as a proxy for pole leader
wins_leader = driver_standings[0].get("Driver",{}).get("familyName","—") if driver_standings else "—"

kpis = [
    {"value": str(total_races),     "label": "Total Races",      "icon": "🏁"},
    {"value": str(completed_count), "label": "Completed",        "icon": "✅", "color": "#4CAF50"},
    {"value": str(remaining_count), "label": "Remaining",        "icon": "📅", "color": "#FFD700"},
    {"value": leader_family,        "label": "Points Leader",    "icon": "🏆", "color": "#E10600",
     "sub": f"{leader_pts} pts"},
    {"value": con_lead,             "label": "Constructors Lead","icon": "🏗️", "color": "#00D2BE",
     "sub": f"{con_pts} pts"},
    {"value": wins_leader,          "label": "Most Wins",        "icon": "🥇", "color": "#FFD700"},
]
render_kpi_row(kpis, cols=6)

divider()

# ── Countdown + Schedule ──────────────────────────────────────────────────────
section_header("Upcoming Grand Prix")
col_cd, col_sched = st.columns(2)
with col_cd:
    render_countdown(next_race)
with col_sched:
    render_session_schedule(next_race)

divider()

# ── Latest Race Results ───────────────────────────────────────────────────────
section_header("Latest Race Results")

if last_race and results:
    r_name   = last_race.get("raceName","")
    r_round  = last_race.get("round","")
    r_date   = last_race.get("date","")
    circuit  = last_race.get("Circuit",{}).get("circuitName","")
    country  = last_race.get("Circuit",{}).get("Location",{}).get("country","")
    flag     = get_country_flag(country)

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;flex-wrap:wrap;">
        <span style="font-size:1.1rem;font-weight:700;">{flag} {r_name}</span>
        <span style="font-size:0.8rem;color:var(--text-muted);">
            Round {r_round} · {format_date(r_date)} · {circuit}
        </span>
    </div>
    """, unsafe_allow_html=True)
    render_race_results_table(results[:10])
    with st.expander("View full results"):
        render_race_results_table(results)
else:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:1.5rem;">
        <div style="color:var(--text-muted);">No race results yet for this season.</div>
    </div>""", unsafe_allow_html=True)

divider()

# ── Standings preview ─────────────────────────────────────────────────────────
section_header("Championship Standings")
tab_d, tab_c = st.tabs(["🏅 Drivers", "🏗️ Constructors"])
with tab_d:
    if driver_standings:
        render_driver_standings(driver_standings[:10])
        st.caption("Top 10 shown · See full standings in the Standings page")
    else:
        st.info("Driver standings not yet available.")
with tab_c:
    if constructor_standings:
        render_constructor_standings(constructor_standings)
    else:
        st.info("Constructor standings not yet available.")

divider()

# ── Points progression (lazy — only build if data exists) ────────────────────
section_header("Points Progression")

if completed_count == 0:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:1.5rem;">
        <div style="color:var(--text-muted);">Chart will appear after the first race.</div>
    </div>""", unsafe_allow_html=True)
elif driver_standings:
    with st.expander("📈 Show points progression chart (loads race data)", expanded=False):
        with st.spinner("Loading race-by-race data…"):
            import plotly.graph_objects as go
            from services.jolpica_service import get_race_results
            from utils.helpers import make_plotly_layout
            from config.teams import get_team_color

            top5_standings = driver_standings[:5]
            top5_map = {
                s.get("Driver",{}).get("driverId",""): {
                    "name":  s.get("Driver",{}).get("familyName",""),
                    "color": get_team_color(
                        s.get("Constructors",[{}])[0].get("constructorId","")
                        if s.get("Constructors") else ""
                    ),
                }
                for s in top5_standings
            }

            race_labels  = []
            cumulative   = {did: 0.0 for did in top5_map}
            series       = {did: [] for did in top5_map}

            for race in past_races:
                rnd = race.get("round","")
                rr  = get_race_results(season, rnd)
                if not rr:
                    continue
                race_labels.append(race.get("raceName","").replace(" Grand Prix",""))
                pts_map = {
                    r.get("Driver",{}).get("driverId",""): float(r.get("points",0))
                    for r in rr
                }
                for did in top5_map:
                    cumulative[did] += pts_map.get(did, 0)
                    series[did].append(cumulative[did])

            if race_labels:
                fig = go.Figure()
                for did, info in top5_map.items():
                    if series[did]:
                        fig.add_trace(go.Scatter(
                            x=race_labels, y=series[did],
                            name=info["name"], mode="lines+markers",
                            line=dict(color=info["color"], width=2.5),
                            marker=dict(size=5),
                        ))
                l = make_plotly_layout("Championship Points Progression", height=380)
                l["xaxis"]["tickangle"] = -30
                fig.update_layout(**l)
                st.plotly_chart(fig, width='stretch')

divider()

st.markdown(f"""
<div style="text-align:center;padding:1rem 0;color:var(--text-faint);font-size:0.7rem;">
    F1Intel · {season} Formula 1 Season · Not affiliated with Formula 1 or FIA
</div>
""", unsafe_allow_html=True)
