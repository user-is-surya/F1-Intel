"""
F1Intel — Telemetry Center
"""

import streamlit as st
st.set_page_config(page_title="Telemetry — F1Intel", page_icon="📡", layout="wide")

from utils.helpers import load_css, page_header, section_header, divider
from components.sidebar import render_sidebar
from components.telemetry_charts import (
    render_telemetry_comparison, render_delta_time, render_racing_lines,
)
from services.fastf1_service import (
    load_session, get_fastest_lap, get_lap_telemetry, get_pos_data,
    get_session_drivers, get_driver_info_ff1, get_driver_laps, get_laps,
)
from services.jolpica_service import get_schedule
from utils.colors import build_driver_color_map
from utils.formatters import format_laptime
from config.settings import CURRENT_SEASON, FASTF1_MIN_SEASON
from datetime import datetime
import pytz

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Telemetry Center", "Speed · Throttle · Brake · RPM · Gear · DRS · Delta", "📡")

if season < FASTF1_MIN_SEASON:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:2rem;">
        <div style="font-size:1.5rem;margin-bottom:0.5rem;">📡</div>
        <div style="color:var(--text-secondary);">
            FastF1 telemetry data is available from the {FASTF1_MIN_SEASON} season onwards.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

schedule = get_schedule(season)
if not schedule:
    st.markdown('<div class="glass-card" style="padding:1.5rem;text-align:center;color:var(--text-muted);">No schedule available.</div>', unsafe_allow_html=True)
    st.stop()

now = datetime.now(pytz.UTC)

def parse_dt(r):
    try:
        return datetime.fromisoformat(f"{r.get('date','')}T{r.get('time','12:00:00Z').rstrip('Z')}+00:00")
    except Exception:
        return None

past_races = [r for r in schedule if (parse_dt(r) or now) < now]
if not past_races:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2rem;">
        <div style="font-size:1.5rem;margin-bottom:0.5rem;">🏁</div>
        <div style="color:var(--text-secondary);">No completed races yet. Telemetry will be available after the first race.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

session_map = {"Qualifying":"Q","Race":"R","Sprint":"S","Practice 1":"FP1","Practice 2":"FP2","Practice 3":"FP3"}
past_options = {f"Round {r.get('round')} — {r.get('raceName','')}": r for r in past_races}

col_r, col_s = st.columns(2)
with col_r:
    sel_race = st.selectbox("Race", list(past_options.keys()), key="tel_race")
with col_s:
    sel_sess = st.selectbox("Session", list(session_map.keys()), key="tel_sess")

sel_race_obj = past_options[sel_race]
round_num    = sel_race_obj.get("round","1")
ff1_key      = session_map[sel_sess]
sess_key_id  = f"{season}_{round_num}_{ff1_key}"

load_btn = st.button("📥 Load Session", key="tel_load",
                     help="Downloads session telemetry. First load may take 1–2 minutes.")

if "tel_session" not in st.session_state or st.session_state.get("tel_sess_id") != sess_key_id:
    if load_btn:
        st.session_state["tel_session"]  = None
        st.session_state["tel_sess_id"]  = None

if load_btn:
    with st.spinner(f"Loading {sel_sess} telemetry — may take a minute on first load…"):
        ff1_session = load_session(season, int(round_num), ff1_key)
    if ff1_session:
        st.session_state["tel_session"]  = ff1_session
        st.session_state["tel_sess_id"]  = sess_key_id
        st.session_state["tel_drvs"]     = get_session_drivers(ff1_session)
        st.session_state["tel_colors"]   = build_driver_color_map(
            st.session_state["tel_drvs"], ff1_session)
        st.success("✅ Session loaded")
    else:
        st.markdown("""
        <div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">
            Session data not available for this round / session type.
        </div>""", unsafe_allow_html=True)
        st.stop()

ff1_session = st.session_state.get("tel_session")
if not ff1_session:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2rem;">
        <div style="color:var(--text-muted);font-size:0.95rem;">
            Select a completed race and session, then click <b>Load Session</b>.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

drv_list  = st.session_state.get("tel_drvs", [])
color_map = st.session_state.get("tel_colors", {})

label_map = {}
for d in drv_list:
    info = get_driver_info_ff1(ff1_session, d)
    label_map[f"{d} — {info.get('full_name','')} ({info.get('team','')})"] = d

labels = list(label_map.keys())
if len(labels) < 2:
    st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Not enough driver data in this session.</div>', unsafe_allow_html=True)
    st.stop()

divider()
section_header("Select Drivers to Compare")
c1, c2 = st.columns(2)
with c1:
    sel_d1 = st.selectbox("Driver 1", labels, index=0, key="td1")
with c2:
    sel_d2 = st.selectbox("Driver 2", labels, index=min(1,len(labels)-1), key="td2")

d1 = label_map[sel_d1]
d2 = label_map[sel_d2]

if d1 == d2:
    st.markdown('<div class="glass-card" style="padding:0.8rem;text-align:center;color:var(--text-secondary);">Please select two different drivers.</div>', unsafe_allow_html=True)
    st.stop()

col_lm, _ = st.columns([1,2])
with col_lm:
    lap_mode = st.radio("Lap", ["Fastest Lap","Specific Lap"], horizontal=True, key="lap_mode")

lap_number = None
if lap_mode == "Specific Lap":
    all_laps_df = get_laps(ff1_session)
    if not all_laps_df.empty and "LapNumber" in all_laps_df.columns:
        max_lap = int(all_laps_df["LapNumber"].max())
        col_ln, _ = st.columns([1,3])
        with col_ln:
            lap_number = st.number_input("Lap Number", 1, max_lap, 1, key="lap_n")

# Load telemetry
with st.spinner("Fetching telemetry…"):
    if lap_mode == "Fastest Lap":
        lap1 = get_fastest_lap(ff1_session, d1)
        lap2 = get_fastest_lap(ff1_session, d2)
    else:
        laps1 = get_driver_laps(ff1_session, d1)
        laps2 = get_driver_laps(ff1_session, d2)
        lap1  = laps1[laps1["LapNumber"]==lap_number].iloc[0] if not laps1.empty and lap_number in laps1["LapNumber"].values else None
        lap2  = laps2[laps2["LapNumber"]==lap_number].iloc[0] if not laps2.empty and lap_number in laps2["LapNumber"].values else None

if lap1 is None or lap2 is None:
    st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Lap data not available for one or both drivers.</div>', unsafe_allow_html=True)
    st.stop()

channels = ["Speed","Throttle","Brake","RPM","nGear","DRS","Time"]
tel1 = get_lap_telemetry(lap1, channels)
tel2 = get_lap_telemetry(lap2, channels)
c1c  = color_map.get(d1,"#E10600")
c2c  = color_map.get(d2,"#00D2BE")

info1 = get_driver_info_ff1(ff1_session, d1)
info2 = get_driver_info_ff1(ff1_session, d2)

# Lap time banner
def get_lt(lap):
    try:
        t = lap.get("LapTime") if hasattr(lap,"get") else getattr(lap,"LapTime",None)
        return format_laptime(t) if t else "—"
    except Exception:
        return "—"

divider()
col_l1, col_l2 = st.columns(2)
with col_l1:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;border-top:3px solid {c1c};">
        <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;
                    color:var(--text-muted);margin-bottom:0.3rem;">{info1.get('full_name','Driver 1')}</div>
        <div style="font-size:2rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:{c1c};">{get_lt(lap1)}</div>
        <div style="font-size:0.72rem;color:var(--text-muted);">{info1.get('team','')}</div>
    </div>""", unsafe_allow_html=True)
with col_l2:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;border-top:3px solid {c2c};">
        <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;
                    color:var(--text-muted);margin-bottom:0.3rem;">{info2.get('full_name','Driver 2')}</div>
        <div style="font-size:2rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:{c2c};">{get_lt(lap2)}</div>
        <div style="font-size:0.72rem;color:var(--text-muted);">{info2.get('team','')}</div>
    </div>""", unsafe_allow_html=True)

divider()
tab_tel, tab_delta, tab_line = st.tabs(["📈 Full Telemetry","⏱ Delta Time","🏎 Racing Lines"])
with tab_tel:
    if tel1.empty and tel2.empty:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Telemetry channels not available.</div>', unsafe_allow_html=True)
    else:
        render_telemetry_comparison(tel1, tel2, d1, d2, c1c, c2c)
with tab_delta:
    render_delta_time(tel1, tel2, d1, d2, c1c, c2c)
with tab_line:
    pos1 = get_pos_data(lap1)
    pos2 = get_pos_data(lap2)
    render_racing_lines(pos1, pos2, d1, d2, c1c, c2c)
