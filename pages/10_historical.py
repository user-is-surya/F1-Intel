"""
F1Intel — Historical Archive
All-time records, season championships, driver & team history.
"""

import streamlit as st
st.set_page_config(page_title="Historical — F1Intel", page_icon="📚", layout="wide")

import plotly.graph_objects as go
from utils.helpers import load_css, page_header, section_header, divider, make_plotly_layout
from components.sidebar import render_sidebar
from components.standings_table import render_driver_standings, render_constructor_standings
from services.jolpica_service import (
    get_all_seasons, get_driver_standings, get_constructor_standings,
    get_schedule, get_race_results, get_drivers, get_season_champion
)
from utils.flags import get_flag, get_country_flag
from utils.formatters import format_date
from config.settings import CURRENT_SEASON
from config.teams import get_team_color

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Historical Archive", "All-time records, champions & statistics", "📚")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Champions", "📊 Season Browser",
    "👤 Driver Records", "🏗️ Constructor Records"
])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Champions History
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section_header("F1 World Champions — All Time")

    start_year = st.slider("From Year", min_value=1950, max_value=CURRENT_SEASON,
                            value=2000, key="champ_year")

    years_to_load = list(range(CURRENT_SEASON, start_year - 1, -1))

    with st.spinner(f"Loading champions from {start_year}–{CURRENT_SEASON}…"):
        champ_table_rows = []
        for yr in years_to_load:
            standings = get_driver_standings(yr)
            if not standings:
                continue
            champ     = standings[0]
            driver    = champ.get("Driver", {})
            constr    = champ.get("Constructors", [{}])[0] if champ.get("Constructors") else {}
            name      = f"{driver.get('givenName','')} {driver.get('familyName','')}"
            nat       = driver.get("nationality","")
            team_name = constr.get("name","")
            points    = champ.get("points","")
            wins      = champ.get("wins","")
            flag      = get_flag(nat)
            is_ongoing = (yr == CURRENT_SEASON)
            champ_table_rows.append({
                "Year": f"{yr}*" if is_ongoing else yr,
                "Champion": f"{flag} {name}" + (" (leading)" if is_ongoing else ""),
                "Team": team_name, "Points": points, "Wins": wins,
            })

    if champ_table_rows:
        import pandas as pd
        df_champs = pd.DataFrame(champ_table_rows)
        st.dataframe(df_champs, hide_index=True, width='stretch')
        if years_to_load and years_to_load[0] == CURRENT_SEASON:
            st.caption(f"* {CURRENT_SEASON} season is still in progress — showing current points leader, not a confirmed champion.")

    # ── Most Championships chart ──────────────────────────────────────────
    divider()
    section_header("Most Championships (Modern Era 2000+)")

    from collections import Counter
    champ_counts: Counter = Counter()
    years_modern = list(range(min(CURRENT_SEASON, 2024), 1999, -1))

    with st.spinner("Computing statistics…"):
        for yr in years_modern:
            standings = get_driver_standings(yr)
            if standings:
                drv = standings[0].get("Driver", {})
                family = drv.get("familyName","Unknown")
                champ_counts[family] += 1

    if champ_counts:
        sorted_champs = sorted(champ_counts.items(), key=lambda x: x[1], reverse=True)
        names_c = [x[0] for x in sorted_champs[:15]]
        vals_c  = [x[1] for x in sorted_champs[:15]]

        fig_c = go.Figure(go.Bar(
            x=names_c, y=vals_c,
            marker_color=["#FFD700" if v == max(vals_c) else "#E10600" for v in vals_c],
            hovertemplate="%{x}: %{y} championships<extra></extra>",
        ))
        lc = make_plotly_layout("Most F1 Championships (2000+)", height=360)
        lc["yaxis"]["title"] = "Championships"
        lc["yaxis"]["dtick"] = 1
        fig_c.update_layout(**lc)
        st.plotly_chart(fig_c, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Season Browser
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section_header("Browse Any Season")

    col_sel, _ = st.columns([1, 2])
    with col_sel:
        browse_year = st.selectbox("Season", range(CURRENT_SEASON, 1949, -1),
                                    index=0, key="browse_yr")

    browse_drv_std  = get_driver_standings(browse_year)
    browse_con_std  = get_constructor_standings(browse_year)
    browse_schedule = get_schedule(browse_year)

    # Season summary
    races_n      = len(browse_schedule)
    is_ongoing_b = (browse_year == CURRENT_SEASON)
    winner       = browse_drv_std[0] if browse_drv_std else {}
    drv_champ    = f"{winner.get('Driver',{}).get('givenName','')} {winner.get('Driver',{}).get('familyName','')}" if winner else "—"
    drv_pts      = winner.get("points","—") if winner else "—"
    con_winner   = browse_con_std[0] if browse_con_std else {}
    con_champ    = con_winner.get("Constructor",{}).get("name","—") if con_winner else "—"
    drv_label    = "Driver Leader" if is_ongoing_b else "Driver Champion"
    con_label    = "Constructor Leader" if is_ongoing_b else "Constructor Champion"

    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:1rem;">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;text-align:center;">
            <div>
                <div style="font-size:1.6rem;font-weight:800;">{browse_year}{'*' if is_ongoing_b else ''}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Season</div>
            </div>
            <div>
                <div style="font-size:1.1rem;font-weight:800;color:#FFD700;">{drv_champ}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">{drv_label}</div>
            </div>
            <div>
                <div style="font-size:1.1rem;font-weight:800;color:#00D2BE;">{con_champ}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">{con_label}</div>
            </div>
            <div>
                <div style="font-size:1.6rem;font-weight:800;">{races_n}</div>
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                            color:var(--text-muted);">Races</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if is_ongoing_b:
        st.caption(f"* {browse_year} season is still in progress — standings reflect current points, not final results.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Driver Standings**")
        render_driver_standings(browse_drv_std[:10])
    with c2:
        st.markdown("**Constructor Standings**")
        render_constructor_standings(browse_con_std)

    if browse_schedule:
        divider()
        section_header(f"{browse_year} Race Calendar")
        cal_b_rows = []
        for race in browse_schedule:
            rnd     = race.get("round","")
            r_name  = race.get("raceName","")
            r_date  = race.get("date","")
            circuit = race.get("Circuit",{}).get("circuitName","")
            country = race.get("Circuit",{}).get("Location",{}).get("country","")
            flag    = get_country_flag(country)
            cal_b_rows.append({
                "Rnd": rnd, "Race": f"{flag} {r_name}",
                "Circuit": circuit, "Date": format_date(r_date),
            })
        if cal_b_rows:
            import pandas as pd
            df_cal_b = pd.DataFrame(cal_b_rows)
            st.dataframe(
                df_cal_b, hide_index=True, width='stretch',
                column_config={"Rnd": st.column_config.NumberColumn("Rnd", width="small")},
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Driver Records
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section_header("All-Time Driver Records")

    from services.jolpica_service import get_driver_info, get_driver_career_stats

    # Most wins ever
    section_header("Season Win Leaders (2010+)")
    st.caption("Shows most wins accumulated in a single season per driver.")

    if st.button("Load Win Leaders", key="load_wins"):
        with st.spinner("Computing win leaders…"):
            win_data = {}
            for yr in range(max(2010, CURRENT_SEASON - 10), CURRENT_SEASON + 1):
                std = get_driver_standings(yr)
                for s in std:
                    did  = s.get("Driver",{}).get("driverId","")
                    name = f"{s.get('Driver',{}).get('givenName','')} {s.get('Driver',{}).get('familyName','')}"
                    w    = int(s.get("wins","0"))
                    if did and w > 0:
                        if did not in win_data or w > win_data[did]["wins"]:
                            win_data[did] = {"name": name, "wins": w, "year": yr}

        if win_data:
            sorted_w = sorted(win_data.items(), key=lambda x: x[1]["wins"], reverse=True)[:15]
            names_w  = [v["name"] for _,v in sorted_w]
            vals_w   = [v["wins"] for _,v in sorted_w]
            fig_w = go.Figure(go.Bar(
                x=names_w, y=vals_w,
                marker_color=["#FFD700" if i==0 else "#E10600" for i in range(len(vals_w))],
                hovertemplate="%{x}: %{y} wins (best season)<extra></extra>",
            ))
            lw = make_plotly_layout("Best Single-Season Win Count (last 10 seasons)", height=360)
            lw["xaxis"]["tickangle"] = -30
            lw["yaxis"]["title"] = "Wins"
            fig_w.update_layout(**lw)
            st.plotly_chart(fig_w, width='stretch')
        else:
            st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">No win data found.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Constructor Records
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    section_header("Constructor Championship History")

    with st.spinner("Loading constructor records (2000+)…"):
        con_champ_history: dict[str, int] = {}
        for yr in range(2000, CURRENT_SEASON + 1):
            std = get_constructor_standings(yr)
            if std:
                cname = std[0].get("Constructor",{}).get("name","Unknown")
                con_champ_history[cname] = con_champ_history.get(cname, 0) + 1

    if con_champ_history:
        sorted_con = sorted(con_champ_history.items(), key=lambda x: x[1], reverse=True)
        names_cc = [x[0] for x in sorted_con]
        vals_cc  = [x[1] for x in sorted_con]
        colors_cc = [get_team_color(n.lower().replace(" ","_")) for n in names_cc]

        fig_cc = go.Figure(go.Bar(
            x=names_cc, y=vals_cc,
            marker_color=colors_cc,
            hovertemplate="%{x}: %{y} championships<extra></extra>",
        ))
        lcc = make_plotly_layout("Constructor Championships (2000+)", height=380)
        lcc["xaxis"]["tickangle"] = -30
        lcc["yaxis"]["title"]     = "Championships"
        lcc["yaxis"]["dtick"]     = 1
        fig_cc.update_layout(**lcc)
        st.plotly_chart(fig_cc, width='stretch')

        # Points over time per top constructor
        divider()
        section_header("Points Progression — Top Constructors")

        top_cons = names_cc[:5]
        fig_pts  = go.Figure()
        years_range = list(range(2010, CURRENT_SEASON + 1))

        with st.spinner("Loading constructor points history…"):
            for con_name in top_cons:
                pts_by_yr = []
                for yr in years_range:
                    std = get_constructor_standings(yr)
                    pts = next(
                        (float(s.get("points",0)) for s in std
                         if s.get("Constructor",{}).get("name","") == con_name),
                        0
                    )
                    pts_by_yr.append(pts)

                cid_lookup = con_name.lower().replace(" ","_")
                color = get_team_color(cid_lookup)
                fig_pts.add_trace(go.Scatter(
                    x=years_range, y=pts_by_yr,
                    name=con_name,
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=5),
                ))

        lp_hist = make_plotly_layout("Top Constructor Points per Season (2010+)", height=400)
        lp_hist["xaxis"]["title"]  = "Season"
        lp_hist["yaxis"]["title"]  = "Points"
        fig_pts.update_layout(**lp_hist)
        st.plotly_chart(fig_pts, width='stretch')
