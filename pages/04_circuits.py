"""
F1Intel — Circuit Intelligence Center
Circuit profiles, records, weather, and historical winners.
"""

import streamlit as st
st.set_page_config(page_title="Circuits — F1Intel", page_icon="🗺️", layout="wide")

import plotly.graph_objects as go
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.circuit_card import render_circuit_card, render_circuit_stats_card
from services.jolpica_service import get_circuits, get_schedule, get_circuit_history
from services.weather_service import get_circuit_weather, get_weather_description, get_circuit_coords, is_wet_conditions
from utils.flags import get_country_flag
from config.teams import get_team_color
from utils.formatters import format_date
from config.settings import CURRENT_SEASON

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Circuit Intelligence Center", "Track profiles, lap records & race history", "🗺️")

# ── Load circuits ─────────────────────────────────────────────────────────────
circuits  = get_circuits(season)
schedule  = get_schedule(season)

# Create merged lookup: circuit_id → (circuit, race)
circuit_race_map = {}
for race in schedule:
    cobj = race.get("Circuit", {})
    cid  = cobj.get("circuitId", "")
    circuit_race_map[cid] = (cobj, race)

# Add any circuits not in schedule
for c in circuits:
    cid = c.get("circuitId", "")
    if cid not in circuit_race_map:
        circuit_race_map[cid] = (c, None)

circuit_display_names = {}
for cid, (c, race) in circuit_race_map.items():
    name = c.get("circuitName", cid)
    country = c.get("Location", {}).get("country", "")
    flag = get_country_flag(country)
    label = f"{flag} {name}"
    circuit_display_names[label] = cid

sorted_labels = sorted(circuit_display_names.keys())

# ── Selection ─────────────────────────────────────────────────────────────────
col_sel, _ = st.columns([1, 2])
with col_sel:
    selected_label = st.selectbox("Select Circuit", sorted_labels, key="circuit_sel")

selected_cid   = circuit_display_names.get(selected_label, "")
circuit_obj, race_obj = circuit_race_map.get(selected_cid, ({}, None))
country        = circuit_obj.get("Location", {}).get("country", "")
lat_str        = circuit_obj.get("Location", {}).get("lat", "")
lon_str        = circuit_obj.get("Location", {}).get("long", "")

# ── Circuit card ──────────────────────────────────────────────────────────────
render_circuit_card(circuit_obj, race_obj)

divider()

# ── Circuit stats (static reference data where available) ─────────────────────
# Known circuit stats — future: could be enriched via external API
CIRCUIT_STATS = {
    "bahrain":      {"length":"5.412 km","corners":"15","drs_zones":"3","race_laps":"57","first_gp":"2004","lap_record":"1:31.447 (De Vries 2023)"},
    "jeddah":       {"length":"6.174 km","corners":"27","drs_zones":"3","race_laps":"50","first_gp":"2021","lap_record":"1:30.734 (Leclerc 2022)"},
    "albert_park":  {"length":"5.303 km","corners":"16","drs_zones":"4","race_laps":"58","first_gp":"1996","lap_record":"1:20.235 (Leclerc 2022)"},
    "suzuka":       {"length":"5.807 km","corners":"18","drs_zones":"1","race_laps":"53","first_gp":"1987","lap_record":"1:30.983 (Hamilton 2019)"},
    "shanghai":     {"length":"5.451 km","corners":"16","drs_zones":"2","race_laps":"56","first_gp":"2004","lap_record":"1:32.238 (Bottas 2019)"},
    "miami":        {"length":"5.412 km","corners":"19","drs_zones":"3","race_laps":"57","first_gp":"2022","lap_record":"1:29.708 (Verstappen 2023)"},
    "imola":        {"length":"4.909 km","corners":"19","drs_zones":"1","race_laps":"63","first_gp":"1980","lap_record":"1:15.484 (Hamilton 2020)"},
    "monaco":       {"length":"3.337 km","corners":"19","drs_zones":"1","race_laps":"78","first_gp":"1950","lap_record":"1:12.909 (Leclerc 2021)"},
    "villeneuve":   {"length":"4.361 km","corners":"14","drs_zones":"2","race_laps":"70","first_gp":"1978","lap_record":"1:13.078 (Bottas 2019)"},
    "catalunya":    {"length":"4.657 km","corners":"16","drs_zones":"2","race_laps":"66","first_gp":"1991","lap_record":"1:18.149 (Bottas 2020)"},
    "red_bull_ring":{"length":"4.318 km","corners":"10","drs_zones":"3","race_laps":"71","first_gp":"1970","lap_record":"1:05.619 (Bottas 2020)"},
    "silverstone":  {"length":"5.891 km","corners":"18","drs_zones":"2","race_laps":"52","first_gp":"1950","lap_record":"1:27.097 (Hamilton 2020)"},
    "hungaroring":  {"length":"4.381 km","corners":"14","drs_zones":"1","race_laps":"70","first_gp":"1986","lap_record":"1:16.627 (Hamilton 2020)"},
    "spa":          {"length":"7.004 km","corners":"19","drs_zones":"2","race_laps":"44","first_gp":"1950","lap_record":"1:46.286 (Bottas 2018)"},
    "zandvoort":    {"length":"4.259 km","corners":"14","drs_zones":"2","race_laps":"72","first_gp":"1952","lap_record":"1:11.097 (Verstappen 2021)"},
    "monza":        {"length":"5.793 km","corners":"11","drs_zones":"2","race_laps":"53","first_gp":"1950","lap_record":"1:21.046 (Barrichello 2004)"},
    "marina_bay":   {"length":"4.940 km","corners":"23","drs_zones":"3","race_laps":"62","first_gp":"2008","lap_record":"1:35.867 (Leclerc 2023)"},
    "losail":       {"length":"5.380 km","corners":"16","drs_zones":"2","race_laps":"57","first_gp":"2021","lap_record":"1:24.319 (Russell 2023)"},
    "americas":     {"length":"5.513 km","corners":"20","drs_zones":"2","race_laps":"56","first_gp":"2012","lap_record":"1:36.169 (Leclerc 2019)"},
    "rodriguez":    {"length":"4.304 km","corners":"17","drs_zones":"3","race_laps":"71","first_gp":"1963","lap_record":"1:17.774 (Bottas 2021)"},
    "interlagos":   {"length":"4.309 km","corners":"15","drs_zones":"2","race_laps":"71","first_gp":"1973","lap_record":"1:10.540 (Hamilton 2018)"},
    "las_vegas":    {"length":"6.201 km","corners":"17","drs_zones":"2","race_laps":"50","first_gp":"2023","lap_record":"1:35.490 (Leclerc 2023)"},
    "yas_marina":   {"length":"5.281 km","corners":"16","drs_zones":"2","race_laps":"58","first_gp":"2009","lap_record":"1:26.103 (Verstappen 2021)"},
    "baku":         {"length":"6.003 km","corners":"20","drs_zones":"2","race_laps":"51","first_gp":"2016","lap_record":"1:43.009 (Leclerc 2019)"},
}

CIRCUIT_TAGS: dict[str, list[str]] = {
    "bahrain":["Good Overtaking","High Speed"], "jeddah":["Good Overtaking","Very High Speed"],
    "albert_park":["Difficult Overtaking","High Speed"], "suzuka":["Difficult Overtaking","Very High Speed"],
    "shanghai":["Good Overtaking","High Speed"], "miami":["Good Overtaking","High Speed"],
    "imola":["Difficult Overtaking","Technical"], "monaco":["Very Difficult Overtaking","Low Speed"],
    "villeneuve":["Good Overtaking","Technical"], "catalunya":["Difficult Overtaking","High Speed"],
    "red_bull_ring":["Good Overtaking","Short Lap"], "silverstone":["Good Overtaking","Very High Speed"],
    "hungaroring":["Difficult Overtaking","Technical"], "spa":["Good Overtaking","Very High Speed"],
    "zandvoort":["Difficult Overtaking","Technical"], "monza":["Good Overtaking","Highest Speed"],
    "marina_bay":["Difficult Overtaking","Street Circuit"], "losail":["Good Overtaking","High Speed"],
    "americas":["Good Overtaking","Technical"], "rodriguez":["Difficult Overtaking","High Altitude"],
    "interlagos":["Good Overtaking","Technical"], "las_vegas":["Good Overtaking","Street Circuit"],
    "yas_marina":["Good Overtaking","Twilight Race"], "baku":["Good Overtaking","Street Circuit"],
}

CIRCUIT_BLURBS: dict[str, str] = {
    "bahrain": "The Bahrain International Circuit opens each season under floodlights, its long straights and heavy braking zones rewarding bold overtaking in the desert night.",
    "albert_park": "Set in Melbourne's parklands, Albert Park blends fast, flowing sections with tight chicanes, demanding a finely balanced car across its lakeside lap.",
    "suzuka": "Suzuka's iconic figure-eight layout and flowing Esses make it one of the most technically demanding and beloved circuits on the calendar.",
    "shanghai": "The Shanghai International Circuit's signature corner spirals inward through 270 degrees, testing both car balance and driver precision.",
    "monaco": "The principality's tight, unforgiving streets turn qualifying into the real race, with virtually no margin for error across the entire lap.",
    "silverstone": "The birthplace of Formula 1 combines high-speed corners like Copse and Maggotts-Becketts with a rich motorsport heritage.",
    "spa": "Spa-Francorchamps' elevation changes and the legendary Eau Rouge-Raidillon complex make it a true test of car and driver courage.",
    "monza": "The 'Temple of Speed' is the fastest circuit on the calendar, defined by long straights and heavy braking into tight chicanes.",
    "marina_bay": "Singapore's night race winds through the city's downtown streets, combining brutal humidity with relentless concentration under the lights.",
    "yas_marina": "The season finale at Yas Marina transitions from daylight to dusk, its modern layout offering several genuine overtaking opportunities.",
    "zandvoort": "The historic dunes circuit returned to the calendar with banked corners and a tight, flowing layout through the Dutch coastline.",
    "interlagos": "Interlagos' anti-clockwise layout and unpredictable São Paulo weather have produced some of the sport's most dramatic title deciders.",
    "baku": "Baku's street circuit pairs the longest straight on the calendar with an impossibly tight castle-section, inviting high-speed drama.",
    "las_vegas": "Racing down the Strip at midnight, this circuit combines long straights with a unique atmosphere unlike anywhere else on the calendar.",
}

# ── Browse All Circuits (card grid) ────────────────────────────────────────────
with st.expander(f"🗺️ Browse All {season} Circuits", expanded=False):
    cols_per_row = 3
    items = list(circuit_race_map.items())
    for row_start in range(0, len(items), cols_per_row):
        row_items = items[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (cid_b, (cobj_b, race_b)) in zip(cols, row_items):
            with col:
                cname_b   = cobj_b.get("circuitName", cid_b)
                loc_b     = cobj_b.get("Location", {})
                country_b = loc_b.get("country", "")
                city_b    = loc_b.get("locality", "")
                flag_b    = get_country_flag(country_b)
                stats_b   = CIRCUIT_STATS.get(cid_b, {})
                tags_b    = CIRCUIT_TAGS.get(cid_b, [])

                st.markdown(f"""
<div class="glass-card" style="padding:1rem;height:100%;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
        <div>
            <div style="font-size:1.05rem;font-weight:800;">{cname_b}</div>
            <div style="font-size:0.78rem;color:var(--text-muted);">{flag_b} {city_b}, {country_b}</div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;margin:0.6rem 0;font-size:0.78rem;">
        <div><span style="color:var(--text-muted);">Length</span><br>
             <b>{stats_b.get('length','—')}</b></div>
        <div><span style="color:var(--text-muted);">Corners</span><br>
             <b>{stats_b.get('corners','—')}</b></div>
        <div><span style="color:var(--text-muted);">First GP</span><br>
             <b>{stats_b.get('first_gp','—')}</b></div>
        <div><span style="color:var(--text-muted);">DRS Zones</span><br>
             <b>{stats_b.get('drs_zones','—')}</b></div>
    </div>
    <div style="margin:0.4rem 0;">{' '.join(f'<span style="background:var(--overlay-soft);padding:2px 8px;border-radius:10px;font-size:0.65rem;margin-right:4px;">{t}</span>' for t in tags_b)}</div>
    <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-top:0.6rem;">Lap Record</div>
    <div style="font-size:0.85rem;font-weight:700;font-family:'JetBrains Mono',monospace;">{stats_b.get('lap_record','—')}</div>
</div>
""", unsafe_allow_html=True)

divider()

section_header(f"{circuit_obj.get('circuitName', selected_label)} — Detailed View")
stats = CIRCUIT_STATS.get(selected_cid, {})
blurb = CIRCUIT_BLURBS.get(selected_cid, "")
tags  = CIRCUIT_TAGS.get(selected_cid, [])

if tags:
    tag_html = " ".join(
        f'<span style="background:var(--overlay-soft);padding:3px 10px;'
        f'border-radius:12px;font-size:0.7rem;margin-right:5px;">{t}</span>'
        for t in tags
    )
    st.markdown(f'<div style="margin-bottom:0.6rem;">{tag_html}</div>', unsafe_allow_html=True)

if blurb:
    st.markdown(
        f'<div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;'
        f'margin-bottom:0.8rem;">{blurb}</div>',
        unsafe_allow_html=True,
    )

render_circuit_stats_card(stats)

divider()

# ── Weather forecast ──────────────────────────────────────────────────────────
section_header("Weather Forecast")

try:
    lat = float(lat_str)
    lon = float(lon_str)
except Exception:
    coords = get_circuit_coords(selected_cid)
    if coords:
        lat, lon = coords
    else:
        lat, lon = None, None

if lat and lon:
    with st.spinner("Fetching weather…"):
        weather_data = get_circuit_weather(lat, lon)

    if weather_data:
        current = weather_data.get("current", {})
        daily   = weather_data.get("daily", {})

        temp     = current.get("temperature_2m", "—")
        humidity = current.get("relative_humidity_2m", "—")
        wind     = current.get("wind_speed_10m", "—")
        wcode    = current.get("weather_code", 0)
        precip   = current.get("precipitation", 0)
        w_desc, w_icon = get_weather_description(wcode)
        is_wet   = is_wet_conditions(wcode)

        wet_style = "border:1px solid rgba(0,103,255,0.4);" if is_wet else ""
        st.markdown(f"""
        <div class="glass-card" style="{wet_style}">
            <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;
                        color:var(--text-muted);margin-bottom:0.8rem;">Current Conditions · {country}</div>
            <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
                <div style="font-size:3rem;">{w_icon}</div>
                <div>
                    <div style="font-size:2rem;font-weight:800;">{temp}°C</div>
                    <div style="font-size:0.9rem;color:var(--text-secondary);">{w_desc}</div>
                </div>
                <div style="display:flex;gap:1.5rem;margin-left:auto;">
                    <div style="text-align:center;">
                        <div style="font-size:1.2rem;font-weight:700;">💧 {humidity}%</div>
                        <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;">Humidity</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:1.2rem;font-weight:700;">💨 {wind} km/h</div>
                        <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;">Wind</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:1.2rem;font-weight:700;">🌧️ {precip} mm</div>
                        <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;">Precip</div>
                    </div>
                </div>
            </div>
            {('<div style="margin-top:0.8rem;padding:0.4rem 0.8rem;background:rgba(0,103,255,0.15);border-radius:6px;font-size:0.82rem;color:#6699FF;">⚠️ Possible wet race conditions</div>' if is_wet else '')}
        </div>
        """, unsafe_allow_html=True)

        # 7-day forecast
        if daily:
            dates     = daily.get("time", [])
            codes     = daily.get("weather_code", [])
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precip_d  = daily.get("precipitation_sum", [])

            if dates:
                cols = st.columns(min(7, len(dates)))
                for i, (date, code, tmax, tmin, prec) in enumerate(
                    zip(dates, codes, temps_max, temps_min, precip_d)
                ):
                    if i >= len(cols):
                        break
                    desc, icon = get_weather_description(code)
                    with cols[i]:
                        from datetime import datetime
                        try:
                            day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
                        except Exception:
                            day_name = date

                        st.markdown(f"""
                        <div class="glass-card" style="text-align:center;padding:0.6rem 0.3rem;">
                            <div style="font-size:0.7rem;color:var(--text-secondary);">{day_name}</div>
                            <div style="font-size:1.6rem;margin:0.3rem 0;">{icon}</div>
                            <div style="font-size:0.82rem;font-weight:700;">{tmax:.0f}°</div>
                            <div style="font-size:0.72rem;color:var(--text-muted);">{tmin:.0f}°</div>
                            {f'<div style="font-size:0.65rem;color:#6699FF;margin-top:0.2rem;">{prec:.1f}mm</div>' if prec > 0 else ''}
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Weather data unavailable.")
else:
    st.info("Circuit coordinates not available for weather lookup.")

divider()

# ── Historical winners ─────────────────────────────────────────────────────────
section_header("Historical Race Winners")

with st.spinner("Loading circuit history…"):
    circuit_history = get_circuit_history(selected_cid, limit=20)

if circuit_history:
    hist_rows = []
    for race in circuit_history:
        year     = race.get("season", "")
        r_name   = race.get("raceName", "")
        results  = race.get("Results", [])
        if not results:
            continue
        winner   = results[0]
        drv      = winner.get("Driver", {})
        constr   = winner.get("Constructor", {})
        name     = f"{drv.get('givenName','')} {drv.get('familyName','')}"
        nat      = drv.get("nationality","")
        flag     = get_country_flag(nat)
        team     = constr.get("name","")
        lap_time = winner.get("FastestLap",{}).get("Time",{}).get("time","") if winner.get("FastestLap") else ""
        hist_rows.append({
            "Year": year, "Race": r_name, "Winner": f"{flag} {name}",
            "Team": team, "Fastest Lap": lap_time,
        })

    if hist_rows:
        import pandas as pd
        df_hist = pd.DataFrame(hist_rows)
        st.dataframe(df_hist, hide_index=True, width='stretch')

    # Winners by nationality pie
    from collections import Counter
    from utils.flags import get_flag, get_country_flag
    nationalities = []
    for race in circuit_history:
        res = race.get("Results", [])
        if res:
            nationalities.append(res[0].get("Driver", {}).get("nationality", "Unknown"))

    if nationalities:
        divider()
        section_header("Winners by Nationality")
        counts = Counter(nationalities)
        fig_pie = go.Figure(go.Pie(
            labels=[f"{get_flag(n)} {n}" for n in counts.keys()],
            values=list(counts.values()),
            hole=0.45,
            marker=dict(line=dict(color="rgba(0,0,0,0.5)", width=1)),
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=350,
            margin=dict(l=20,r=20,t=30,b=20),
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_pie, width='stretch')
else:
    st.info(f"No historical data available for this circuit.")

divider()

# ── Circuit list ──────────────────────────────────────────────────────────────
section_header(f"All {season} Circuits")

if schedule:
    cal_rows = []
    for race in schedule:
        rnd     = race.get("round", "")
        r_name  = race.get("raceName", "")
        r_date  = race.get("date", "")
        cobj    = race.get("Circuit", {})
        c_name  = cobj.get("circuitName", "")
        country = cobj.get("Location", {}).get("country", "")
        city    = cobj.get("Location", {}).get("locality", "")
        flag    = get_country_flag(country)
        cal_rows.append({
            "Rnd": rnd, "Race": f"{flag} {r_name}", "Circuit": c_name,
            "Location": f"{city}, {country}", "Date": format_date(r_date),
        })

    if cal_rows:
        import pandas as pd
        df_cal = pd.DataFrame(cal_rows)
        st.dataframe(
            df_cal, hide_index=True, width='stretch',
            column_config={"Rnd": st.column_config.NumberColumn("Rnd", width="small")},
        )
