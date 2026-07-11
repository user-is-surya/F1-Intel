"""
F1Intel — Live Leaderboard Component
FIA timing-wall style live race leaderboard.
"""

from __future__ import annotations
import streamlit as st
from utils.helpers import tire_badge_html
from utils.formatters import format_gap, format_laptime


def render_live_header(session_info: dict | None = None) -> None:
    """Render session header with live indicator."""
    if not session_info:
        st.markdown("""
        <div style="text-align:center;padding:1rem;">
            <span class="status-badge status-live">⚡ LIVE</span>
        </div>
        """, unsafe_allow_html=True)
        return

    session_name = session_info.get("session_name", "Race")
    meeting_name = session_info.get("meeting_name", "")
    circuit      = session_info.get("circuit_short_name", "")

    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:1rem;">
        <div style="display:flex;align-items:center;justify-content:center;gap:1rem;flex-wrap:wrap;">
            <span class="status-badge status-live">● LIVE</span>
            <span style="font-size:1.1rem;font-weight:700;">{meeting_name}</span>
            <span style="font-size:0.85rem;color:var(--text-secondary);">{session_name} · {circuit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_leaderboard_row(pos: int, driver_number: int, driver_name: str,
                             team_color: str, gap: str, interval: str,
                             last_lap: str, best_lap: str,
                             compound: str, tire_age: int,
                             pit_stops: int, drs: bool = False,
                             is_fastest: bool = False) -> str:
    """Return HTML for a single leaderboard row."""
    pos_color = ""
    if pos == 1:   pos_color = "color:#FFD700;"
    elif pos == 2: pos_color = "color:#C0C0C0;"
    elif pos == 3: pos_color = "color:#CD7F32;"

    fastest_class = 'background:rgba(128,0,255,0.12);' if is_fastest else ''
    drs_html      = '<span style="color:#00FF88;font-size:0.65rem;font-weight:700;">DRS</span>' if drs else ''
    tire_html     = tire_badge_html(compound)

    return f"""
    <div class="live-row {'leader' if pos == 1 else ''}" style="{fastest_class}">
        <div style="font-weight:800;font-size:0.9rem;{pos_color}">{pos}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                    color:{team_color};font-weight:700;">{driver_number}</div>
        <div style="font-weight:600;font-size:0.88rem;">
            {driver_name}
            <span style="margin-left:4px;">{drs_html}</span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                    color:var(--text-secondary);">{gap}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                    color:var(--text-secondary);">{interval}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                    {'color:#9C27B0;font-weight:700;' if is_fastest else ''}">{last_lap}</div>
        <div style="display:flex;align-items:center;gap:4px;">
            {tire_html}
            <span style="font-size:0.65rem;color:var(--text-muted);">{tire_age}L</span>
            <span style="font-size:0.65rem;color:var(--text-muted);">P{pit_stops}</span>
        </div>
    </div>
    """


def render_leaderboard_header() -> str:
    """Return HTML for the leaderboard column headers."""
    return """
    <div style="display:grid;grid-template-columns:32px 28px 1fr 80px 80px 80px 60px;
                gap:0.5rem;padding:0.4rem 0.8rem;
                border-bottom:2px solid rgba(225,6,0,0.3);margin-bottom:0.3rem;">
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">POS</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">No.</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">Driver</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">Gap</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">Int.</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">Last Lap</div>
        <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;
                    color:var(--text-muted);">Tyre</div>
    </div>
    """


def render_race_control_feed(messages: list[dict]) -> None:
    """Render race control message feed."""
    if not messages:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:1.5rem;">
            <span style="color:var(--text-muted);font-size:0.85rem;">
                No race control messages
            </span>
        </div>
        """, unsafe_allow_html=True)
        return

    rows = ""
    for msg in reversed(messages[-20:]):  # show last 20
        category = msg.get("category", "")
        message  = msg.get("message", "")
        flag_str = msg.get("flag", "")
        lap_num  = msg.get("lap_number", "")
        date_str = msg.get("date", "")

        # Color code by category
        cat_color = {
            "Flag": "#FFD700",
            "SafetyCar": "#FFA500",
            "Drs": "#00FF88",
            "Other": "var(--text-secondary)",
            "ChequeredFlag": "#FFFFFF",
        }.get(category, "var(--text-secondary)")

        # Flag color
        flag_color = {
            "GREEN":  "#00FF88",
            "YELLOW": "#FFD700",
            "RED":    "#E10600",
            "SC":     "#FFA500",
            "VSC":    "#FFD700",
        }.get(str(flag_str).upper(), "")
        flag_dot = f'<span style="color:{flag_color};margin-right:4px;">●</span>' if flag_color else ""

        time_str = ""
        if date_str:
            try:
                from datetime import datetime
                import pytz
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = ""

        lap_html = f'<span style="color:var(--text-muted);font-size:0.7rem;">Lap {lap_num}</span>' if lap_num else ""

        rows += f"""
        <div style="padding:0.5rem 0;border-bottom:1px solid var(--divider-soft);">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.2rem;">
                <span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;
                             color:{cat_color};">{flag_dot}{category}</span>
                <div style="display:flex;gap:0.5rem;align-items:center;">
                    {lap_html}
                    <span style="font-size:0.68rem;color:var(--text-muted);
                                 font-family:'JetBrains Mono',monospace;">{time_str}</span>
                </div>
            </div>
            <div style="font-size:0.82rem;color:var(--text-primary);">{message}</div>
        </div>
        """

    st.markdown(f"""
    <div class="glass-card" style="max-height:400px;overflow-y:auto;">
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.14em;color:var(--text-muted);margin-bottom:0.6rem;">
            📻 Race Control
        </div>
        {rows}
    </div>
    """, unsafe_allow_html=True)
