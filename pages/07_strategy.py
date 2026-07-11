"""
F1Intel — Strategy Center
"""

import streamlit as st
st.set_page_config(page_title="Strategy — F1Intel", page_icon="🔧", layout="wide")

import plotly.graph_objects as go
import numpy as np
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.strategy_charts import (
    render_strategy_timeline, render_lap_time_evolution,
    render_tire_degradation, render_pit_stop_summary,
)
from services.fastf1_service import (
    load_session_basic, get_laps, get_tire_stints,
    get_session_drivers, get_driver_info_ff1,
)
from services.jolpica_service import get_schedule, get_pit_stops
from services.strategy_sim_service import (
    get_real_stint_plan, get_driver_compounds_used,
    simulate_alternate_strategy, get_actual_race_time,
    estimate_position_change, DEFAULT_PIT_LOSS_SECONDS, VALID_COMPOUNDS,
)
from utils.colors import build_driver_color_map
from config.settings import CURRENT_SEASON, FASTF1_MIN_SEASON, TIRE_COLORS
from datetime import datetime
import pytz

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Strategy Center", "Tire compounds, pit windows & race strategy", "🔧")

if season < FASTF1_MIN_SEASON:
    st.markdown(f'<div class="glass-card" style="padding:2rem;text-align:center;color:var(--text-secondary);">FastF1 strategy data available from {FASTF1_MIN_SEASON} onwards.</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="glass-card" style="text-align:center;padding:2rem;color:var(--text-secondary);">No completed races yet in this season.</div>', unsafe_allow_html=True)
    st.stop()

past_opts = {f"Round {r.get('round')} — {r.get('raceName','')}": r for r in past_races}
col_sel, _ = st.columns([1,2])
with col_sel:
    sel = st.selectbox("Race", list(past_opts.keys()), key="strat_race")

sel_race  = past_opts[sel]
round_num = sel_race.get("round","1")

load_btn = st.button("📥 Load Race Strategy Data", key="strat_load")
sess_key_id = f"{season}_{round_num}_R"

if "strat_sess" not in st.session_state or st.session_state.get("strat_sid") != sess_key_id:
    if load_btn:
        st.session_state["strat_sess"] = None

if load_btn:
    with st.spinner("Loading race data…"):
        ff1 = load_session_basic(season, int(round_num), "R")
    st.session_state["strat_sess"] = ff1
    st.session_state["strat_sid"]  = sess_key_id
    if not ff1:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Race session data not available.</div>', unsafe_allow_html=True)

ff1 = st.session_state.get("strat_sess")
if not ff1:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2rem;">
        <div style="color:var(--text-muted);">Select a race and click <b>Load Race Strategy Data</b>.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

all_laps   = get_laps(ff1)
stints     = get_tire_stints(ff1)
drv_list   = get_session_drivers(ff1)
color_map  = build_driver_color_map(drv_list, ff1)
total_laps = int(all_laps["LapNumber"].max()) if not all_laps.empty and "LapNumber" in all_laps.columns else 70

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Strategy Timeline","📉 Lap Evolution",
    "🔥 Tire Degradation","🛑 Pit Windows","⚡ Compound Analysis",
    "🔮 What If"
])

with tab1:
    section_header("Race Strategy Timeline")
    if not stints.empty:
        render_strategy_timeline(stints, total_laps)
    else:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Stint data not available.</div>', unsafe_allow_html=True)
    pits_api = get_pit_stops(season, round_num)
    if pits_api:
        divider()
        section_header("Pit Stop Summary")
        render_pit_stop_summary(pits_api)

with tab2:
    section_header("Lap Time Evolution")
    if not all_laps.empty:
        labels2 = [f"{d} — {get_driver_info_ff1(ff1,d).get('full_name','')}" for d in drv_list]
        sel2    = st.multiselect("Drivers", labels2,
                                  default=labels2[:6] if len(labels2)>=6 else labels2, key="strat_drvs")
        abbrs2  = [x.split(" — ")[0] for x in sel2]
        if abbrs2:
            render_lap_time_evolution(all_laps, abbrs2, color_map)
    else:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Lap data not available.</div>', unsafe_allow_html=True)

with tab3:
    section_header("Tire Degradation")
    if not all_laps.empty and drv_list:
        labels3 = [f"{d} — {get_driver_info_ff1(ff1,d).get('full_name','')}" for d in drv_list]
        sel3    = st.selectbox("Driver", labels3, key="strat_deg")
        abbr3   = sel3.split(" — ")[0]
        render_tire_degradation(all_laps, abbr3, color_map)

        if not stints.empty:
            divider()
            section_header("Stint Length Distribution")
            fig_b = go.Figure()
            for comp in stints["Compound"].unique():
                c_data = stints[stints["Compound"]==comp]["laps"]
                fig_b.add_trace(go.Box(y=c_data, name=str(comp),
                    marker_color=TIRE_COLORS.get(str(comp).upper(),"#888"),
                    boxpoints="all", jitter=0.3, pointpos=-1.8))
            lb = make_plotly_layout("Stint Length by Compound", height=340)
            lb["yaxis"]["title"] = "Laps in Stint"
            fig_b.update_layout(**lb)
            st.plotly_chart(fig_b, width='stretch')
    else:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Lap data not available.</div>', unsafe_allow_html=True)

with tab4:
    section_header("Pit Window Analysis")
    if not stints.empty and not all_laps.empty:
        pit_wins = stints.groupby("Driver").apply(
            lambda g: g.sort_values("Stint")["first_lap"].values[1:].tolist() if len(g)>1 else [],
            include_groups=False
        ).reset_index()
        pit_wins.columns = ["Driver","pit_laps"]
        fig_pw = go.Figure()
        for _, row in pit_wins.iterrows():
            drv_     = row["Driver"]
            pls      = row["pit_laps"]
            if not pls:
                continue
            fig_pw.add_trace(go.Scatter(
                x=pls, y=[drv_]*len(pls), mode="markers",
                marker=dict(color=color_map.get(drv_,"#888"),size=14,symbol="diamond",
                            line=dict(color="white",width=1)),
                name=drv_, showlegend=False,
                hovertemplate=f"<b>{drv_}</b> pit on Lap %{{x}}<extra></extra>",
            ))
        l_pw = make_plotly_layout("Pit Stop Lap by Driver", height=max(320,len(drv_list)*30))
        l_pw["xaxis"]["title"] = "Lap Number"
        l_pw["xaxis"]["range"] = [0, total_laps]
        fig_pw.update_layout(**l_pw)
        st.plotly_chart(fig_pw, width='stretch')
    else:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Strategy data not available.</div>', unsafe_allow_html=True)

with tab5:
    section_header("Compound Usage")
    if not stints.empty:
        counts = stints["Compound"].value_counts()
        colors_pie = [TIRE_COLORS.get(str(c).upper(),"#888") for c in counts.index]
        fig_pie = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.4,
            marker=dict(colors=colors_pie, line=dict(color="rgba(0,0,0,0.4)",width=1)),
        ))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                               height=320, margin=dict(l=20,r=20,t=30,b=20),
                               title=dict(text="Compound Distribution",font=dict(color="white",size=13)),
                               legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_pie, width='stretch')

        if not all_laps.empty and "Compound" in all_laps.columns and "LapTime" in all_laps.columns:
            divider()
            section_header("Avg Lap Time by Compound")
            lc2 = all_laps.copy()
            lc2["LapSec"] = lc2["LapTime"].dt.total_seconds()
            lc2 = lc2.dropna(subset=["LapSec","Compound"])
            med = lc2["LapSec"].median()
            lc2 = lc2[lc2["LapSec"] < med * 1.10]
            avg_c = lc2.groupby("Compound")["LapSec"].agg(["mean","std","count"]).reset_index()
            fig_avg = go.Figure()
            for _, row in avg_c.iterrows():
                comp = str(row["Compound"]).upper()
                fig_avg.add_trace(go.Bar(
                    x=[comp], y=[row["mean"]],
                    error_y=dict(type="data", array=[row["std"]], visible=True),
                    marker_color=TIRE_COLORS.get(comp,"#888"), name=comp,
                    hovertemplate=f"{comp}<br>Avg: %{{y:.3f}}s · n={int(row['count'])}<extra></extra>",
                ))
            la = make_plotly_layout("Avg Lap Time by Compound", height=300)
            la["yaxis"]["title"] = "Seconds"
            la["showlegend"] = False
            fig_avg.update_layout(**la)
            st.plotly_chart(fig_avg, width='stretch')
    else:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Compound data not available.</div>', unsafe_allow_html=True)


with tab6:
    section_header("Strategy Simulator — \"What If\"")
    st.markdown(
        '<div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:0.8rem;">'
        'Explore an alternate pit strategy for this race using real tyre degradation '
        'data from the session. Pick a driver, change their stops, and see the '
        'estimated time and position impact.</div>',
        unsafe_allow_html=True,
    )

    if all_laps.empty or stints.empty:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Lap and stint data not available for this race.</div>', unsafe_allow_html=True)
    else:
        labels6 = [f"{d} — {get_driver_info_ff1(ff1,d).get('full_name','')}" for d in drv_list]
        sel6    = st.selectbox("Driver", labels6, key="whatif_driver")
        abbr6   = sel6.split(" — ")[0]

        real_plan = get_real_stint_plan(stints, abbr6)
        if not real_plan:
            st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">No stint data found for this driver.</div>', unsafe_allow_html=True)
        else:
            # ── Show the driver's REAL strategy as reference ──────────────
            divider()
            st.markdown(
                '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
                'color:var(--text-muted);margin-bottom:0.4rem;">Actual Strategy (Real Race Data)</div>',
                unsafe_allow_html=True,
            )
            real_strip = " → ".join(
                f'{r["Compound"].upper()} (laps {int(r["first_lap"])}-{int(r["last_lap"])})'
                for r in real_plan
            )
            st.markdown(
                f'<div class="glass-card" style="padding:0.7rem 1rem;font-family:\'JetBrains Mono\',monospace;'
                f'font-size:0.85rem;">{real_strip}</div>',
                unsafe_allow_html=True,
            )

            actual_time = get_actual_race_time(all_laps, abbr6)

            divider()
            st.markdown(
                '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
                'color:var(--text-muted);margin-bottom:0.4rem;">Build Your Alternate Strategy</div>',
                unsafe_allow_html=True,
            )

            n_stints = st.slider("Number of stints", 1, 4,
                                  value=min(len(real_plan), 4), key="whatif_nstints")

            # Build editable stint plan — default to evenly-spaced laps
            default_breaks = np.linspace(1, total_laps, n_stints + 1).astype(int).tolist()
            new_plan = []
            cols_per_stint = st.columns(n_stints)
            for i in range(n_stints):
                with cols_per_stint[i]:
                    st.markdown(f"**Stint {i+1}**")
                    default_compound = (real_plan[i]["Compound"].upper()
                                        if i < len(real_plan) else "MEDIUM")
                    compound_i = st.selectbox(
                        "Tyre", VALID_COMPOUNDS,
                        index=VALID_COMPOUNDS.index(default_compound) if default_compound in VALID_COMPOUNDS else 1,
                        key=f"whatif_comp_{i}",
                    )
                    start_default = default_breaks[i] if i == 0 else default_breaks[i] + 1
                    if i == 0:
                        start_lap_i = 1
                        st.caption("Starts lap 1")
                    else:
                        start_lap_i = st.number_input(
                            f"Pit on lap", min_value=2, max_value=total_laps - 1,
                            value=min(default_breaks[i], total_laps - 1), key=f"whatif_start_{i}",
                        )
                    new_plan.append({"compound": compound_i, "start_lap": start_lap_i})

            # Convert start laps into start/end ranges
            for i in range(len(new_plan)):
                new_plan[i]["start_lap"] = 1 if i == 0 else new_plan[i]["start_lap"]
                end = (new_plan[i+1]["start_lap"] - 1) if i + 1 < len(new_plan) else total_laps
                new_plan[i]["end_lap"] = end

            # Validate plan covers laps without gaps/overlaps
            plan_valid = all(new_plan[i]["end_lap"] >= new_plan[i]["start_lap"] for i in range(len(new_plan)))
            if len(new_plan) > 1:
                plan_valid = plan_valid and all(
                    new_plan[i+1]["start_lap"] > new_plan[i]["start_lap"] for i in range(len(new_plan)-1)
                )

            pit_loss_input = st.slider(
                "Assumed pit stop time loss (seconds)", 15.0, 30.0,
                value=DEFAULT_PIT_LOSS_SECONDS, step=0.5, key="whatif_pitloss",
                help="Average time lost entering/exiting the pits and the stationary stop itself. "
                     "Not circuit-specific — adjust if you know this track's pit lane is faster/slower.",
            )

            divider()
            run_sim = st.button("▶️ Run Simulation", key="whatif_run", type="primary")

            if run_sim:
                if not plan_valid:
                    st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:#E10600;">Stint pit laps must increase in order. Adjust the lap numbers above.</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("Simulating alternate strategy from real tyre data…"):
                        result = simulate_alternate_strategy(
                            all_laps, stints, abbr6, total_laps, new_plan,
                            pit_loss_seconds=pit_loss_input,
                        )

                    if actual_time is None:
                        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">Could not compute this driver\'s actual race time for comparison.</div>', unsafe_allow_html=True)
                    else:
                        pos_info = estimate_position_change(
                            all_laps, abbr6, result["total_time"], actual_time
                        )
                        delta = result["total_time"] - actual_time
                        delta_color = "#4CAF50" if delta < 0 else ("#E10600" if delta > 0 else "var(--text-secondary)")
                        delta_label = f"{'−' if delta < 0 else '+'}{abs(delta):.1f}s"

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Simulated Time Delta", delta_label)
                        with c2:
                            est_pos = pos_info.get("estimated_position")
                            act_pos = pos_info.get("actual_position_by_time")
                            pos_delta = (act_pos - est_pos) if (est_pos and act_pos) else None
                            pos_display = f"P{est_pos}" if est_pos else "—"
                            pos_sub = (f"vs actual P{act_pos}" if act_pos else None)
                            st.metric("Estimated Finish", pos_display, delta=pos_sub if pos_sub else None)
                        with c3:
                            st.metric("Pit Stops", result["pit_stops"])

                        st.markdown(
                            f'<div style="margin-top:0.3rem;font-size:0.85rem;color:{delta_color};font-weight:600;">'
                            f'{"Faster" if delta < 0 else "Slower" if delta > 0 else "No change"} than the real race '
                            f'by {abs(delta):.1f} seconds over {total_laps} laps.</div>',
                            unsafe_allow_html=True,
                        )

                        if result["warnings"]:
                            for w in result["warnings"]:
                                st.caption(f"⚠️ {w}")

                        divider()
                        st.markdown(
                            '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
                            'color:var(--text-muted);margin-bottom:0.4rem;">Simulated Lap Time Trace</div>',
                            unsafe_allow_html=True,
                        )
                        fig_sim = go.Figure()
                        fig_sim.add_trace(go.Scatter(
                            y=result["lap_times"], mode="lines",
                            line=dict(color="#E10600", width=2),
                            name="Simulated pace",
                        ))
                        l_sim = make_plotly_layout("Projected Lap Times — Alternate Strategy", height=320)
                        l_sim["xaxis"]["title"] = "Lap"
                        l_sim["yaxis"]["title"] = "Lap Time (s)"
                        fig_sim.update_layout(**l_sim)
                        st.plotly_chart(fig_sim, width='stretch')

                        st.caption(
                            "This is an estimate based on this driver's own real degradation curve "
                            "(or field-average where their own data is unavailable). It assumes a clear "
                            "track with no traffic, overtaking difficulty, or safety car interruptions, "
                            "and a fixed average pit-lane time loss rather than this circuit's exact value."
                        )
