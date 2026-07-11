"""
F1Intel — Race Analysis Center
"""

import streamlit as st
st.set_page_config(page_title="Race Analysis — F1Intel", page_icon="📊", layout="wide")

from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.standings_table import render_race_results_table, render_qualifying_table
from components.strategy_charts import (
    render_strategy_timeline, render_lap_time_evolution,
    render_tire_degradation, render_pit_stop_summary,
)
from services.jolpica_service import (
    get_schedule, get_race_results, get_qualifying_results,
    get_sprint_results, get_pit_stops, get_fastest_laps,
)
from services.fastf1_service import (
    load_session_basic, get_laps, get_tire_stints,
    get_sector_times, get_session_drivers, get_driver_info_ff1,
)
from utils.colors import build_driver_color_map
from utils.flags import get_country_flag, get_flag
from utils.formatters import format_date
from config.settings import CURRENT_SEASON, FASTF1_MIN_SEASON
from config.teams import get_team_color

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Race Analysis Center", "Results, strategy & session data", "📊")

schedule = get_schedule(season)
if not schedule:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2rem;">
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">📅</div>
        <div style="color:var(--text-secondary);">No race schedule found for this season.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

race_options = {f"Round {r.get('round')} — {r.get('raceName','')}": r for r in schedule}

session_map = {
    "Race": "R", "Qualifying": "Q", "Sprint": "S",
    "Sprint Qualifying": "SQ", "Practice 1": "FP1",
    "Practice 2": "FP2", "Practice 3": "FP3",
}

col_race, col_sess = st.columns(2)
with col_race:
    sel_label = st.selectbox("Race", list(race_options.keys()), key="ra_race")
with col_sess:
    session_type = st.selectbox("Session (for lap/sector data)", list(session_map.keys()), key="ra_sess")

selected_race = race_options[sel_label]
round_num     = selected_race.get("round","1")
race_name     = selected_race.get("raceName","")
race_date     = selected_race.get("date","")
circuit       = selected_race.get("Circuit",{}).get("circuitName","")
country       = selected_race.get("Circuit",{}).get("Location",{}).get("country","")
flag          = get_country_flag(country)

# Check if race is in the future
from datetime import datetime
import pytz
now = datetime.now(pytz.UTC)
try:
    race_dt = datetime.fromisoformat(
        f"{race_date}T{selected_race.get('time','12:00:00Z').rstrip('Z')}+00:00"
    )
    race_is_future = race_dt > now
except Exception:
    race_is_future = False

st.markdown(f"""
<div class="glass-card" style="padding:0.7rem 1.2rem;margin-bottom:0.5rem;">
    <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
        <span style="font-size:1.2rem;font-weight:800;">{flag} {race_name}</span>
        <span style="font-size:0.82rem;color:var(--text-muted);">
            Round {round_num} · {format_date(race_date)} · {circuit}
        </span>
        {'<span class="status-badge status-upcoming">Upcoming</span>' if race_is_future else
         '<span class="status-badge status-finished">Completed</span>'}
    </div>
</div>
""", unsafe_allow_html=True)

if race_is_future:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2.5rem;">
        <div style="font-size:2.5rem;margin-bottom:0.8rem;">🏁</div>
        <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.4rem;">Race hasn't happened yet</div>
        <div style="color:var(--text-muted);font-size:0.9rem;">
            Results, lap times and analysis will be available after the race weekend.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()


def _parse_dur(d):
    """Parse pit stop duration which may be 'SS.mmm' or 'MM:SS.mmm'."""
    try:
        if d is None or d == "":
            return 999.0
        s = str(d)
        if ":" in s:
            parts = s.split(":")
            return float(parts[0])*60 + float(parts[1])
        return float(s)
    except Exception:
        return 999.0

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏁 Results", "⏱ Lap Times", "🔧 Strategy", "🛑 Pit Stops", "⚡ Sectors"
])

# ── Tab 1: Results ─────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        section_header("Race Results")
        race_results = get_race_results(season, round_num)
        if race_results:
            render_race_results_table(race_results)
        else:
            st.markdown('<div class="glass-card" style="padding:1.2rem;text-align:center;color:var(--text-muted);">Race results not published yet.</div>', unsafe_allow_html=True)

    with c2:
        section_header("Qualifying Results")
        qual = get_qualifying_results(season, round_num)
        if qual:
            render_qualifying_table(qual)
        else:
            st.markdown('<div class="glass-card" style="padding:1.2rem;text-align:center;color:var(--text-muted);">Qualifying results not available.</div>', unsafe_allow_html=True)

    sprint = get_sprint_results(season, round_num)
    if sprint:
        divider()
        section_header("Sprint Results")
        render_race_results_table(sprint)

    fl = get_fastest_laps(season, round_num)
    if fl:
        divider()
        section_header("Fastest Laps")
        fl_table_rows = []
        for r in fl:
            drv    = r.get("Driver",{})
            constr = r.get("Constructor",{})
            fastest= r.get("FastestLap",{})
            fl_t   = fastest.get("Time",{}).get("time","—") if fastest else "—"
            fl_lap = fastest.get("lap","—") if fastest else "—"
            spd    = fastest.get("AverageSpeed",{}) if fastest else {}
            spd_v  = spd.get("speed","—") if spd else "—"
            spd_u  = spd.get("units","") if spd else ""
            name   = f"{drv.get('givenName','')} {drv.get('familyName','')}"
            flag_d = get_flag(drv.get("nationality",""))
            fl_table_rows.append({
                "Time": fl_t, "Driver": f"{flag_d} {name}",
                "Team": constr.get("name",""), "Lap": fl_lap,
                "Avg Speed": f"{spd_v} {spd_u}".strip(),
            })
        if fl_table_rows:
            import pandas as pd
            df_fl = pd.DataFrame(fl_table_rows)
            st.dataframe(df_fl, hide_index=True, width='stretch')

# ── Tab 2: Lap Times ────────────────────────────────────────────────────────
with tab2:
    if season < FASTF1_MIN_SEASON:
        st.info(f"FastF1 telemetry data is available from {FASTF1_MIN_SEASON} onwards.")
    else:
        ff1_key = session_map.get(session_type,"R")
        load_btn = st.button(f"📥 Load {session_type} Data", key="ra_load_lap")
        if "ra_ff1" not in st.session_state or st.session_state.get("ra_ff1_round") != f"{round_num}_{ff1_key}":
            st.session_state["ra_ff1"] = None

        if load_btn:
            with st.spinner(f"Loading {session_type}…"):
                sess = load_session_basic(season, int(round_num), ff1_key)
            if sess:
                st.session_state["ra_ff1"]       = sess
                st.session_state["ra_ff1_round"]  = f"{round_num}_{ff1_key}"
            else:
                st.session_state["ra_ff1"] = None
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Session data not available for this round.</div>', unsafe_allow_html=True)

        sess = st.session_state.get("ra_ff1")
        if sess:
            all_laps  = get_laps(sess)
            drv_list  = get_session_drivers(sess)
            color_map = build_driver_color_map(drv_list, sess)

            if not all_laps.empty:
                drv_labels = [
                    f"{d} — {get_driver_info_ff1(sess,d).get('full_name','')}"
                    for d in drv_list
                ]
                sel_drvs = st.multiselect("Drivers", drv_labels,
                    default=drv_labels[:6] if len(drv_labels)>=6 else drv_labels,
                    key="ra_drvs")
                abbrs = [d.split(" — ")[0] for d in sel_drvs]
                if abbrs:
                    section_header("Lap Time Evolution")
                    render_lap_time_evolution(all_laps, abbrs, color_map)
            else:
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">No lap data found in this session.</div>', unsafe_allow_html=True)
        elif not load_btn:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:1.5rem;">
                <div style="color:var(--text-muted);font-size:0.9rem;">
                    Click <b>Load Data</b> above to fetch lap times via FastF1.
                </div>
            </div>""", unsafe_allow_html=True)

# ── Tab 3: Strategy ─────────────────────────────────────────────────────────
with tab3:
    if season < FASTF1_MIN_SEASON:
        st.info(f"Strategy data available from {FASTF1_MIN_SEASON} onwards.")
    else:
        load_s = st.button("📥 Load Race Strategy Data", key="ra_load_strat")
        if "ra_strat_sess" not in st.session_state or st.session_state.get("ra_strat_rnd") != round_num:
            st.session_state["ra_strat_sess"] = None

        if load_s:
            with st.spinner("Loading race strategy…"):
                s2 = load_session_basic(season, int(round_num), "R")
            st.session_state["ra_strat_sess"] = s2
            st.session_state["ra_strat_rnd"]  = round_num
            if not s2:
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Race session data not available.</div>', unsafe_allow_html=True)

        s2 = st.session_state.get("ra_strat_sess")
        if s2:
            stints   = get_tire_stints(s2)
            all_laps = get_laps(s2)
            total_l  = int(all_laps["LapNumber"].max()) if not all_laps.empty and "LapNumber" in all_laps.columns else 70

            section_header("Strategy Timeline")
            if not stints.empty:
                render_strategy_timeline(stints, total_l)
            else:
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Stint data not available.</div>', unsafe_allow_html=True)

            divider()
            section_header("Tire Degradation")
            drv_list2  = get_session_drivers(s2)
            if drv_list2:
                labels2  = [f"{d} — {get_driver_info_ff1(s2,d).get('full_name','')}" for d in drv_list2]
                sel2     = st.selectbox("Driver", labels2, key="ra_deg")
                abbr2    = sel2.split(" — ")[0]
                cm2      = build_driver_color_map(drv_list2, s2)
                if not all_laps.empty:
                    render_tire_degradation(all_laps, abbr2, cm2)
        elif not load_s:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:1.5rem;">
                <div style="color:var(--text-muted);">Click <b>Load Race Strategy Data</b> to begin.</div>
            </div>""", unsafe_allow_html=True)

# ── Tab 4: Pit Stops ─────────────────────────────────────────────────────────
with tab4:
    section_header("Pit Stop Summary")
    pits = get_pit_stops(season, round_num)
    if pits:
        render_pit_stop_summary(pits)
        divider()
        pit_table_rows = []
        for ps in sorted(pits, key=lambda x: _parse_dur(x.get("duration","999"))):
            did  = ps.get("driverId","")
            lap  = ps.get("lap","—")
            stop = ps.get("stop","—")
            dur  = ps.get("duration","—")
            t    = ps.get("time","—")
            try:
                df = float(dur)
                ds = f"{df:.3f}s"
            except Exception:
                ds = str(dur)
            pit_table_rows.append({
                "Driver": did, "Stop": f"Stop {stop}", "Lap": f"Lap {lap}",
                "Time of Day": t, "Duration": ds,
            })
        if pit_table_rows:
            import pandas as pd
            df_pits = pd.DataFrame(pit_table_rows)
            st.dataframe(df_pits, hide_index=True, width='stretch')
    else:
        st.markdown('<div class="glass-card" style="padding:1.5rem;text-align:center;color:var(--text-muted);">Pit stop data not available for this race.</div>', unsafe_allow_html=True)

# ── Tab 5: Sectors ──────────────────────────────────────────────────────────
with tab5:
    if season < FASTF1_MIN_SEASON:
        st.info(f"Sector data available from {FASTF1_MIN_SEASON} onwards.")
    else:
        import plotly.graph_objects as go
        ff1_key_s = session_map.get(session_type,"Q")
        load_sec  = st.button(f"📥 Load Sector Data ({session_type})", key="ra_load_sec")
        if "ra_sec_sess" not in st.session_state or st.session_state.get("ra_sec_rnd") != f"{round_num}_{ff1_key_s}":
            st.session_state["ra_sec_sess"] = None

        if load_sec:
            with st.spinner("Loading sector data…"):
                s3 = load_session_basic(season, int(round_num), ff1_key_s)
            st.session_state["ra_sec_sess"] = s3
            st.session_state["ra_sec_rnd"]  = f"{round_num}_{ff1_key_s}"
            if not s3:
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Session data not available.</div>', unsafe_allow_html=True)

        s3 = st.session_state.get("ra_sec_sess")
        if s3:
            sec_df = get_sector_times(s3)
            if not sec_df.empty:
                drv_list3  = get_session_drivers(s3)
                color_map3 = build_driver_color_map(drv_list3, s3)
                best = sec_df.groupby("Driver").apply(lambda g: g.nsmallest(1,"LapTime")).reset_index(drop=True)
                for col_name, label in [("Sector1Time","S1"),("Sector2Time","S2"),("Sector3Time","S3")]:
                    if col_name not in best.columns:
                        continue
                    b = best.dropna(subset=[col_name]).copy()
                    b[f"_s"] = b[col_name].dt.total_seconds()
                    b = b.sort_values("_s")
                    fig = go.Figure(go.Bar(
                        x=b["Driver"], y=b["_s"],
                        marker_color=[color_map3.get(d,"#888") for d in b["Driver"]],
                        hovertemplate="Driver: %{x}<br>Time: %{y:.3f}s<extra></extra>",
                    ))
                    l = make_plotly_layout(f"Best {label} Times", height=270)
                    l["yaxis"]["title"] = "Seconds"
                    fig.update_layout(**l)
                    st.plotly_chart(fig, width='stretch')
            else:
                st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Sector data not found.</div>', unsafe_allow_html=True)
        elif not load_sec:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:1.5rem;">
                <div style="color:var(--text-muted);">Click <b>Load Sector Data</b> to begin.</div>
            </div>""", unsafe_allow_html=True)
