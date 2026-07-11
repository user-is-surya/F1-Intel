"""
F1Intel — Live Race Center

REWORKED: live timing previously polled the OpenF1 API every 5-6 seconds
via st.fragment + streamlit_autorefresh, which (a) needs a funded/paid
OpenF1 tier to work reliably during an actual live session, and (b) was
one of the heaviest things running on any page, keeping a background
poll loop alive the whole time a user sat on this tab.

Until live data is funded, this page:
  1. Shows a clear, honest notice instead of pretending to be live.
  2. Displays the final classification of the most recently completed
     race (from Jolpica — already cached, already free) as a "timing
     wall" style table, so the page still has real, useful content.
  3. Keeps a lightweight general-F1-knowledge AI chat tab that doesn't
     depend on any live session data.
"""

import streamlit as st
st.set_page_config(page_title="Live — F1Intel", page_icon="⚡", layout="wide")

from datetime import datetime
import pytz
from html import escape as _esc

from utils.helpers import load_css, page_header, section_header, divider, driver_link_html
from components.sidebar import render_sidebar
from services.jolpica_service import get_schedule, get_last_race_results, get_fastest_laps
from config.settings import CURRENT_SEASON, CONTACT_EMAIL
from config.teams import get_team_color
from utils.flags import get_flag
from utils.formatters import format_date

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("Live Race Center", "Timing wall & race control", "⚡")

# ── Funding notice — always shown; this page does not attempt any live
#    polling until OpenF1's paid live tier is funded. ─────────────────────────
st.markdown(f"""
<div class="funding-banner">
    <div class="fb-icon">🔒</div>
    <div class="fb-text">
        <b>Live timing requires funding.</b> Live timing, telemetry, and real-time race data are provided through premium data services that require a paid subscription. We hope to bring live timing to F1Intel in the future as the project grows. If you'd like to help
        fund or build this out, reach out at
        <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.
    </div>
</div>
""", unsafe_allow_html=True)

now = datetime.now(pytz.UTC)


def parse_race_dt(race):
    try:
        d = race.get("date", ""); t = race.get("time", "12:00:00Z").rstrip("Z")
        return datetime.fromisoformat(f"{d}T{t}+00:00")
    except Exception:
        return None


schedule = get_schedule(season)
past_races   = [r for r in schedule if (parse_race_dt(r) or now) < now]
future_races = [r for r in schedule if (parse_race_dt(r) or now) >= now]
next_race    = future_races[0] if future_races else None

tab_timing, tab_ai = st.tabs(["📊 Last Race — Final Classification", "🤖 F1 Knowledge Chat"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Static "timing wall" for the most recent completed race
# ════════════════════════════════════════════════════════════════════════════
with tab_timing:
    last_race, results = get_last_race_results(season)

    if next_race:
        next_country = next_race.get("Circuit", {}).get("Location", {}).get("country", "")
        next_flag    = get_flag(next_country) if next_country else ""
        next_dt      = parse_race_dt(next_race)
        days_to      = (next_dt - now).days if next_dt else None
        days_txt     = f" · {days_to} day{'s' if days_to != 1 else ''} away" if days_to is not None and days_to >= 0 else ""
        st.markdown(f"""
        <div class="glass-card" style="padding:0.7rem 1.1rem;margin-bottom:1rem;
             display:flex;align-items:center;gap:0.7rem;flex-wrap:wrap;">
            <span class="status-badge status-upcoming">📅 UP NEXT</span>
            <span style="font-weight:700;">{next_flag} {next_race.get('raceName','')}</span>
            <span style="color:var(--text-muted);font-size:0.85rem;">
                {format_date(next_race.get('date',''))}{days_txt}
            </span>
        </div>
        """, unsafe_allow_html=True)

    if not last_race or not results:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:2.2rem;">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">🏁</div>
            <div style="color:var(--text-muted);">
                No completed race yet this season — check back after the first Grand Prix.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    r_name  = last_race.get("raceName", "")
    r_round = last_race.get("round", "")
    r_date  = last_race.get("date", "")
    circuit = last_race.get("Circuit", {}).get("circuitName", "")
    country = last_race.get("Circuit", {}).get("Location", {}).get("country", "")
    flag    = get_flag(country)

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;flex-wrap:wrap;">
        <span class="status-badge status-finished">⏸ FINAL CLASSIFICATION</span>
        <span style="font-size:1.1rem;font-weight:700;">{flag} {r_name}</span>
        <span style="font-size:0.8rem;color:var(--text-muted);">
            Round {r_round} · {format_date(r_date)} · {circuit}
        </span>
    </div>
    """, unsafe_allow_html=True)

    fastest_laps = get_fastest_laps(season, r_round)
    fastest_driver_id = None
    if fastest_laps:
        fastest_driver_id = fastest_laps[0].get("Driver", {}).get("driverId")

    rows = ""
    for r in results:
        pos         = r.get("position", "—")
        driver      = r.get("Driver", {})
        constructor = r.get("Constructor", {})
        laps        = r.get("laps", "—")
        status      = r.get("status", "—")
        points      = r.get("points", "0")
        time_val    = r.get("Time", {}).get("time", "—") if r.get("Time") else status
        fastest     = r.get("FastestLap", {})
        fl_time     = fastest.get("Time", {}).get("time", "") if fastest else ""
        fl_rank     = fastest.get("rank", "") if fastest else ""

        given  = _esc(driver.get("givenName", ""))
        family = _esc(driver.get("familyName", ""))
        driver_id = driver.get("driverId", "")
        nationality = driver.get("nationality", "")
        team_color  = get_team_color(constructor.get("constructorId", ""))
        team_name   = _esc(constructor.get("name", ""))
        drv_flag    = get_flag(nationality)

        try:
            pi = int(pos)
            pc = "var(--f1-gold)" if pi == 1 else "var(--f1-silver)" if pi == 2 else "var(--f1-bronze)" if pi == 3 else "var(--text-secondary)"
        except Exception:
            pc = "var(--text-secondary)"

        fl_badge = (
            f'<span class="sector-chip" style="background:rgba(180,100,255,0.15);'
            f'color:#b464ff;margin-left:6px;">⚡ {_esc(fl_time)}</span>'
            if fl_rank == "1" else ""
        )

        # NOTE: this HTML is intentionally built with ZERO leading whitespace
        # per line. Streamlit's markdown renderer follows CommonMark, where a
        # line indented 4+ spaces gets treated as a literal/preformatted code
        # block instead of being parsed as HTML — which is exactly what showed
        # up as raw <td>/<tr> tags printed as plain text instead of a table.
        driver_cell = (
            f'<span style="display:inline-block;width:3px;height:14px;background:{team_color};'
            f'border-radius:2px;margin-right:7px;vertical-align:middle;"></span> '
            f'{drv_flag} {driver_link_html(f"{given} {family}", driver_id)}'
        )
        rows += (
            "<tr>"
            f'<td class="pos" style="color:{pc};font-weight:800;">{_esc(str(pos))}</td>'
            f"<td>{driver_cell}</td>"
            f'<td style="color:var(--text-secondary);font-size:0.82rem;">{team_name}</td>'
            f'<td style="font-family:\'JetBrains Mono\',monospace;font-size:0.82rem;">'
            f"{_esc(str(time_val))}{fl_badge}</td>"
            f'<td style="text-align:center;color:var(--text-secondary);">{_esc(str(laps))}</td>'
            f'<td style="text-align:right;font-weight:700;">{_esc(str(points))}</td>'
            "</tr>"
        )

    table_html = (
        '<div style="overflow-x:auto;"><table class="timing-table">'
        "<thead><tr>"
        "<th>POS</th><th>DRIVER</th><th>TEAM</th><th>TIME / STATUS</th>"
        '<th style="text-align:center;">LAPS</th><th style="text-align:right;">PTS</th>'
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    st.caption(f"Final classification for {r_name} - "
               f"not live timing.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — General F1 knowledge chat (no live-session dependency)
# ════════════════════════════════════════════════════════════════════════════
with tab_ai:
    from services.ai_service import generate_chat_reply, is_configured as ai_is_configured

    if not ai_is_configured():
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;padding:2.2rem;">
            <div style="font-size:2rem;margin-bottom:0.6rem;">🔑</div>
            <div style="font-size:1.05rem;font-weight:700;margin-bottom:0.5rem;">
                F1 Knowledge Chat needs a Gemini API key
            </div>
            <div style="font-size:0.85rem;color:var(--text-muted);max-width:480px;margin:0 auto;">
                Copy <code>.streamlit/secrets.toml.example</code> to
                <code>.streamlit/secrets.toml</code> and paste your free Gemini
                API key from <a href="https://aistudio.google.com" target="_blank"
                style="color:var(--f1-red);">aistudio.google.com</a> under the
                <code>[gemini]</code> section.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.8rem;">
            Ask general Formula 1 questions — rules, history, technical concepts,
            driver/team records. This chat doesn't have live session data (see
            the funding notice above), so it won't have this-second race info.
        </div>""", unsafe_allow_html=True)

        CHAT_SYSTEM_PROMPT = """You are an experienced Formula 1 race engineer and \
analyst embedded in F1Intel. Answer general Formula 1 questions — rules, history, \
technical concepts, regulations, driver/team history, how things work — clearly \
and accurately, the way a knowledgeable F1 engineer would explain things to a \
curious fan.  Keep answers concise — 2-5 sentences for most questions, longer only if genuinely \
needed. Speak like a real engineer: direct, technical when warranted, no fluff."""

        if "live_chat_history" not in st.session_state:
            st.session_state.live_chat_history = []

        chat_container = st.container(height=420)
        with chat_container:
            if not st.session_state.live_chat_history:
                st.markdown("""
                <div style="text-align:center;padding:2rem;color:var(--text-faint);font-size:0.85rem;">
                    Ask something like "what's the DRS rule?" or
                    "who has the most pole positions?" to get started.
                </div>""", unsafe_allow_html=True)
            for msg in st.session_state.live_chat_history:
                avatar = "🧑" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["text"])

        user_q = st.chat_input("Ask F1Intel")

        if user_q and user_q.strip():
            st.session_state.live_chat_history.append({"role": "user", "text": user_q.strip()})
            with chat_container:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(user_q.strip())
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Thinking…"):
                        history_for_api = st.session_state.live_chat_history[:-1][-8:]
                        api_messages = history_for_api + [{"role": "user", "text": user_q.strip()}]
                        result = generate_chat_reply(api_messages, system_instruction=CHAT_SYSTEM_PROMPT)
                    if result["ok"]:
                        st.markdown(result["text"])
                        st.session_state.live_chat_history.append({"role": "assistant", "text": result["text"]})
                    else:
                        error_text = f"⚠️ {result['error']}"
                        st.markdown(error_text)
                        st.session_state.live_chat_history.append({"role": "assistant", "text": error_text})

        if st.session_state.live_chat_history:
            if st.button("🗑️ Clear conversation", key="live_chat_clear"):
                st.session_state.live_chat_history = []
