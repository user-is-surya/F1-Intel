"""
F1Intel — Standings — premium card style matching the reference images.
Each entry is a full-width card with position, driver/team info, stats, and points.
"""
from __future__ import annotations
import streamlit as st
from utils.flags import get_flag, get_country_flag
from utils.formatters import format_points
from config.teams import get_team_color
from utils.helpers import driver_display_name, driver_link_html
from html import escape as _e


# ── Constructor logo SVG letters (simple colored badge fallback) ──────────────
def _team_logo_html(cid: str, name: str, color: str, size: int = 40) -> str:
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "??"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:10px;'
        f'background:{color};display:flex;align-items:center;justify-content:center;'
        f'font-size:{size//3}px;font-weight:900;color:var(--text-primary);'
        f'flex-shrink:0;letter-spacing:-0.02em;">{initials}</div>'
    )


def render_driver_standings(standings: list[dict], highlight_top: int = 3) -> None:
    if not standings:
        st.info("No standings data available.")
        return

    leader_pts = float(standings[0].get("points", "0")) if standings else 0

    for entry in standings:
        pos         = int(entry.get("position", 0))
        driver      = entry.get("Driver", {})
        constructor = entry.get("Constructors", [{}])[0] if entry.get("Constructors") else {}
        pts         = float(entry.get("points", "0"))
        wins        = int(entry.get("wins", "0"))
        nationality = driver.get("nationality", "")
        cid         = constructor.get("constructorId", "")
        team_name   = constructor.get("name", "")
        team_color  = get_team_color(cid)
        flag        = get_flag(nationality)
        given       = _e(driver.get("givenName", ""))
        family      = _e(driver.get("familyName", ""))
        driver_id   = driver.get("driverId", "")
        number      = driver.get("permanentNumber", "")
        gap         = leader_pts - pts

        # Position colors
        pos_colors  = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
        pos_color   = pos_colors.get(pos, "var(--text-muted)")
        border_color= pos_colors.get(pos, team_color)

        # Points gained today (last race)
        pts_str = format_points(pts)
        gap_str = f"−{format_points(gap)}" if gap > 0 else "LEADER"
        gap_color = "#4CAF50" if gap == 0 else "var(--text-muted)"

        driver_badge = (
            f'<div style="background:{team_color};color:var(--text-primary);border-radius:8px;'
            f'padding:3px 9px;font-size:0.68rem;font-weight:800;letter-spacing:0.06em;'
            f'display:inline-block;">'
            f'{"".join(w[0] for w in (given+" "+family).split()[:3]).upper()}'
            f'</div>'
        )

        num_badge = (
            f'<div style="background:{team_color}22;border:1px solid {team_color}55;'
            f'color:{team_color};border-radius:8px;width:44px;height:44px;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:1rem;font-weight:900;font-family:\'JetBrains Mono\',monospace;'
            f'flex-shrink:0;">{number}</div>'
        )

        # Podium glow
        glow = f"box-shadow:0 0 20px {team_color}30;" if pos <= 3 else ""

        st.markdown(f"""
<div style="background:linear-gradient(135deg,{team_color}10 0%,var(--bg-card-solid) 60%);
            border:1px solid {border_color}40;border-left:4px solid {border_color};
            border-radius:14px;padding:1rem 1.2rem;margin-bottom:0.5rem;{glow}
            display:grid;grid-template-columns:52px 56px 1fr auto;
            gap:0.8rem;align-items:center;">

  <div style="text-align:center;">
    <div style="font-size:2rem;font-weight:900;color:{pos_color};line-height:1;">{pos}</div>
    <div style="font-size:0.58rem;color:var(--text-muted);text-transform:uppercase;
                letter-spacing:0.1em;">P{pos}</div>
  </div>

  {num_badge}

  <div>
    <div style="font-size:1.1rem;font-weight:800;letter-spacing:-0.01em;">
      {flag} {driver_link_html(f"{given} {family}", driver_id)}
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
      <span style="font-size:0.72rem;color:var(--text-secondary);">● {team_name}</span>
      {driver_badge}
    </div>
    <div style="display:flex;gap:1.2rem;margin-top:6px;">
      <span style="font-size:0.72rem;color:var(--text-muted);">🏆 {wins} wins</span>
      <span style="font-size:0.72rem;color:{gap_color};">{gap_str}</span>
    </div>
  </div>

  <div style="text-align:right;">
    <div style="font-size:2rem;font-weight:900;letter-spacing:-0.02em;">{pts_str}</div>
    <div style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;
                color:var(--text-muted);">PTS</div>
  </div>

</div>""", unsafe_allow_html=True)


def render_constructor_standings(standings: list[dict]) -> None:
    if not standings:
        st.info("No constructor standings available.")
        return

    leader_pts = float(standings[0].get("points", "0")) if standings else 0

    for entry in standings:
        pos         = int(entry.get("position", 0))
        constructor = entry.get("Constructor", {})
        pts         = float(entry.get("points", "0"))
        wins        = int(entry.get("wins", "0"))
        cid         = constructor.get("constructorId", "")
        name        = _e(constructor.get("name", "Unknown"))
        nat         = constructor.get("nationality", "")
        team_color  = get_team_color(cid)
        flag        = get_country_flag(nat)
        gap         = leader_pts - pts

        pos_colors  = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
        pos_color   = pos_colors.get(pos, "var(--text-muted)")
        border_color= pos_colors.get(pos, team_color)

        pts_str = format_points(pts)
        gap_str = f"−{format_points(gap)}" if gap > 0 else "LEADER"
        gap_color = "#4CAF50" if gap == 0 else "var(--text-muted)"

        logo_html = _team_logo_html(cid, name, team_color, 48)
        glow      = f"box-shadow:0 0 20px {team_color}30;" if pos <= 3 else ""

        st.markdown(f"""
<div style="background:linear-gradient(135deg,{team_color}10 0%,var(--bg-card-solid) 60%);
            border:1px solid {border_color}40;border-left:4px solid {border_color};
            border-radius:14px;padding:1rem 1.2rem;margin-bottom:0.5rem;{glow}
            display:grid;grid-template-columns:52px 56px 1fr auto;
            gap:0.8rem;align-items:center;">

  <div style="text-align:center;">
    <div style="font-size:2rem;font-weight:900;color:{pos_color};line-height:1;">{pos}</div>
    <div style="font-size:0.58rem;color:var(--text-muted);text-transform:uppercase;
                letter-spacing:0.1em;">P{pos}</div>
  </div>

  {logo_html}

  <div>
    <div style="font-size:1.2rem;font-weight:900;letter-spacing:-0.02em;">{flag} {name}</div>
    <div style="display:flex;gap:1.2rem;margin-top:5px;">
      <span style="font-size:0.72rem;color:var(--text-muted);">🏆 {wins} wins</span>
      <span style="font-size:0.72rem;color:{gap_color};">{gap_str}</span>
    </div>
  </div>

  <div style="text-align:right;">
    <div style="font-size:2rem;font-weight:900;letter-spacing:-0.02em;">{pts_str}</div>
    <div style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;
                color:var(--text-muted);">PTS</div>
  </div>

</div>""", unsafe_allow_html=True)


def render_race_results_table(results: list[dict]) -> None:
    if not results:
        st.info("No results available.")
        return

    rows = ""
    for r in results:
        pos         = r.get("position", "—")
        driver      = r.get("Driver", {})
        constructor = r.get("Constructor", {})
        grid        = r.get("grid", "—")
        laps        = r.get("laps", "—")
        status      = r.get("status", "—")
        points      = r.get("points", "0")
        time_val    = r.get("Time", {}).get("time", "—") if r.get("Time") else status
        fastest     = r.get("FastestLap", {})
        fl_rank     = fastest.get("rank", "") if fastest else ""
        fl_time     = fastest.get("Time", {}).get("time", "") if fastest else ""

        name       = _e(driver_display_name(driver))
        nationality= driver.get("nationality", "")
        cid        = constructor.get("constructorId", "")
        team_name  = _e(constructor.get("name", ""))
        team_color = get_team_color(cid)
        flag       = get_flag(nationality)
        driver_id  = driver.get("driverId", "")

        try:
            pi = int(pos)
            pc = ("#FFD700" if pi==1 else "#C0C0C0" if pi==2 else "#CD7F32" if pi==3
                  else "var(--text-primary)")
        except Exception:
            pc = "var(--text-primary)"

        fl_html = (f'<span style="color:#cc88ff;font-size:0.72rem;margin-left:4px;">⚡ {_e(fl_time)}</span>'
                   if fl_rank == "1" else "")

        rows += f"""<tr>
            <td class="pos" style="color:{pc};font-weight:800;">{_e(str(pos))}</td>
            <td><span style="display:inline-block;width:3px;height:14px;background:{team_color};
                     border-radius:2px;margin-right:7px;vertical-align:middle;"></span>
                {flag} {driver_link_html(name, driver_id)}</td>
            <td style="color:var(--text-secondary);font-size:0.8rem;">{team_name}</td>
            <td style="font-family:'Courier New',monospace;font-size:0.8rem;">
                {_e(str(time_val))} {fl_html}</td>
            <td style="text-align:center;color:var(--text-secondary);">{_e(str(laps))}</td>
            <td style="text-align:center;color:var(--text-secondary);">{_e(str(grid))}</td>
            <td style="text-align:right;font-weight:700;">{_e(str(points))}</td>
        </tr>"""

    st.markdown(f"""<div style="overflow-x:auto;"><table class="standings-table">
        <thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th>
        <th>TIME</th><th style="text-align:center;">LAPS</th>
        <th style="text-align:center;">GRID</th><th style="text-align:right;">PTS</th>
        </tr></thead><tbody>{rows}</tbody></table></div>""",
        unsafe_allow_html=True)


def render_qualifying_table(results: list[dict]) -> None:
    if not results:
        st.info("No qualifying data available.")
        return

    rows = ""
    for r in results:
        pos    = r.get("position", "—")
        driver = r.get("Driver", {})
        constr = r.get("Constructor", {})
        q1     = _e(str(r.get("Q1", "—") or "—"))
        q2     = _e(str(r.get("Q2", "—") or "—"))
        q3     = _e(str(r.get("Q3", "—") or "—"))

        name       = _e(driver_display_name(driver))
        nationality= driver.get("nationality", "")
        cid        = constr.get("constructorId", "")
        team_name  = _e(constr.get("name", ""))
        team_color = get_team_color(cid)
        flag       = get_flag(nationality)
        driver_id  = driver.get("driverId", "")

        try:
            pi = int(pos)
            pc = ("#FFD700" if pi==1 else "#C0C0C0" if pi==2 else "#CD7F32" if pi==3
                  else "var(--text-primary)")
        except Exception:
            pc = "var(--text-primary)"

        def q_cell(t):
            if not t or t == "—":
                return '<span style="color:var(--text-faint);">—</span>'
            return f'<span style="font-family:\'Courier New\',monospace;font-size:0.82rem;">{t}</span>'

        rows += f"""<tr>
            <td class="pos" style="color:{pc};font-weight:800;">{_e(str(pos))}</td>
            <td><span style="display:inline-block;width:3px;height:14px;background:{team_color};
                     border-radius:2px;margin-right:7px;vertical-align:middle;"></span>
                {flag} {driver_link_html(name, driver_id)}</td>
            <td style="color:var(--text-secondary);font-size:0.8rem;">{team_name}</td>
            <td>{q_cell(q1)}</td><td>{q_cell(q2)}</td><td>{q_cell(q3)}</td>
        </tr>"""

    st.markdown(f"""<div style="overflow-x:auto;"><table class="standings-table">
        <thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th>
        <th>Q1</th><th>Q2</th><th>Q3</th></tr></thead>
        <tbody>{rows}</tbody></table></div>""",
        unsafe_allow_html=True)
