"""
F1Intel — AI Race Stories
Auto-generated narrative summaries for each Grand Prix weekend, covering
practice, qualifying, sprint (if held), and the race itself — key moments,
stats, turning points, and strategy battles, written like a news recap.

Stories are generated once per race and cached to disk (see
services/race_story_storage.py) so revisiting a race's story is instant
and costs zero additional API calls.

v2 — visual redesign: magazine-style hero header per race, a proper
byline/meta strip instead of a plain "cached" pill, and a card grid for
past stories instead of a bare list.
"""

import streamlit as st
st.set_page_config(page_title="Race Stories — F1Intel", page_icon="📰", layout="wide")

import streamlit.components.v1 as components
from datetime import datetime
import pytz

from utils.helpers import load_css, page_header, divider
from components.sidebar import render_sidebar
from services.jolpica_service import get_schedule
from services.race_story_data import build_race_story_context
from services.race_story_storage import load_story, save_story, delete_story, list_cached_stories
from services.ai_service import generate_text, is_configured
from utils.flags import get_flag
from utils.formatters import format_date
from config.settings import CURRENT_SEASON

load_css()
season = render_sidebar() or CURRENT_SEASON

page_header("AI Race Stories", "Auto-generated narrative recaps of every Grand Prix weekend", "📰")

if not is_configured():
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2.2rem;">
        <div style="font-size:2rem;margin-bottom:0.6rem;">🔑</div>
        <div style="font-size:1.05rem;font-weight:700;margin-bottom:0.5rem;">
            AI Race Stories needs a Gemini API key
        </div>
        <div style="font-size:0.85rem;color:var(--text-muted);max-width:480px;margin:0 auto;">
            Copy <code>.streamlit/secrets.toml.example</code> to
            <code>.streamlit/secrets.toml</code> and paste your free Gemini
            API key from <a href="https://aistudio.google.com" target="_blank"
            style="color:var(--f1-red);">aistudio.google.com</a> under the
            <code>[gemini]</code> section.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

schedule = get_schedule(season)
if not schedule:
    st.markdown('<div class="glass-card" style="padding:1.5rem;text-align:center;color:var(--text-muted);">No schedule available for this season.</div>', unsafe_allow_html=True)
    st.stop()

now = datetime.now(pytz.UTC)


def parse_race_dt(race):
    try:
        d = race.get("date", ""); t = race.get("time", "12:00:00Z").rstrip("Z")
        return datetime.fromisoformat(f"{d}T{t}+00:00")
    except Exception:
        return None


completed_races = [r for r in schedule if (parse_race_dt(r) or now) < now]

if not completed_races:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:2.5rem;">
        <div style="font-size:2rem;margin-bottom:0.6rem;">🏁</div>
        <div style="color:var(--text-muted);">
            No races have happened yet this season. Stories will appear here
            after each Grand Prix weekend.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Race picker ────────────────────────────────────────────────────────────────
race_options = {
    f"Round {r.get('round')} — {get_flag(r.get('Circuit',{}).get('Location',{}).get('country',''))} {r.get('raceName','')}": r
    for r in completed_races
}
default_label = list(race_options.keys())[-1]  # most recent completed race

col_pick, col_status = st.columns([2, 1])
with col_pick:
    sel_label = st.selectbox("Select a race", list(race_options.keys()),
                              index=list(race_options.keys()).index(default_label),
                              key="story_race_sel")

selected_race = race_options[sel_label]
round_num     = selected_race.get("round", "1")
race_name     = selected_race.get("raceName", "")
race_country  = selected_race.get("Circuit", {}).get("Location", {}).get("country", "")
race_circuit  = selected_race.get("Circuit", {}).get("circuitName", "")
race_date     = selected_race.get("date", "")
race_flag     = get_flag(race_country)

cached = load_story(season, round_num)

with col_status:
    if cached:
        gen_time = datetime.fromtimestamp(cached.get("generated_at", 0))
        st.markdown(f"""
        <div class="glass-card" style="padding:0.6rem 1rem;margin-top:1.6rem;font-size:0.78rem;
                    color:var(--text-muted);text-align:center;">
            ✓ Cached · generated {gen_time.strftime('%d %b %Y, %H:%M')}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card" style="padding:0.6rem 1rem;margin-top:1.6rem;font-size:0.78rem;
                    color:var(--text-muted);text-align:center;">
            Not yet generated
        </div>""", unsafe_allow_html=True)

# ── Magazine-style hero header for the selected race ────────────────────────────
st.markdown(f"""
<div class="glass-card fade-in" style="padding:1.6rem 1.8rem;margin:0.8rem 0 1.2rem;
     background:linear-gradient(135deg, rgba(225,6,0,0.08) 0%, var(--bg-card) 55%);
     border-left:4px solid var(--f1-red);position:relative;overflow:hidden;">
    <div style="position:absolute;top:-30px;right:-20px;font-size:7rem;opacity:0.06;line-height:1;">📰</div>
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.16em;
                color:var(--f1-red);margin-bottom:0.4rem;">Race Weekend Recap · Round {round_num}</div>
    <div style="font-size:1.7rem;font-weight:900;letter-spacing:-0.02em;margin-bottom:0.3rem;">
        {race_flag} {race_name}
    </div>
    <div style="font-size:0.85rem;color:var(--text-secondary);">
        {race_circuit} · {format_date(race_date)}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Generate or display ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a veteran Formula 1 journalist writing a complete race weekend recap for a serious motorsport publication. Your writing style is vivid, analytical and fact-based—similar to Autosport, The Race or Motorsport.com. The article should read like a professional race report rather than a simple summary.

Base the story ONLY on the information provided. Never invent facts, quotes, timings, incidents or reasons that are not explicitly supported by the supplied data. If information for a session (Practice, Sprint, Qualifying, etc.) is unavailable, simply omit it instead of guessing.

Before writing, carefully identify every race-defining event from the provided data. Give special attention to:

• Major crashes, spins, retirements and DNFs
• The cause of each major incident (if available)
• Safety Cars, Virtual Safety Cars and Red Flags
• Penalties and steward decisions
• Mechanical failures and reliability issues
• Strategy gambles and pit stop decisions
• Weather changes and track evolution
• Championship implications
• Unexpected performances
• Significant overtakes and defensive battles
• Team orders or intra-team battles
• Any notable off-track developments during the weekend (driver announcements, penalties, technical directives, protests, FIA decisions, contract news, etc.) if present in the supplied data.

IMPORTANT:
A major incident involving a front-running driver (for example, a crash involving Max Verstappen, Lewis Hamilton, Charles Leclerc, Lando Norris, Oscar Piastri, George Russell, etc.) MUST NOT be omitted if it appears in the data. Explain:
- what happened,
- why it happened (if the cause is available),
- how it affected the race,
- and its wider consequences.

Structure the recap using Markdown headings:

# Weekend Overview
Set the scene by describing the circuit, championship context, expectations coming into the weekend, and any notable off-track storylines.

# Practice & Qualifying
Describe how the weekend developed before the race:
- pace shown in practice
- qualifying battles
- standout laps
- surprises
- disappointments
- penalties affecting the grid
- any practice incidents

# The Race
Tell the race as a coherent story from lights out to the chequered flag. Cover:
- the start
- opening-lap battles
- major overtakes
- strategic phases
- Safety Cars/VSCs
- crashes and retirements
- decisive moments
- the closing laps
- the finish

Don't simply list events—connect them into a flowing narrative explaining how one event led to the next.

# Major Incidents
Describe every significant incident separately, including:
- what happened
- why it happened (when known)
- drivers involved
- steward action (if any)
- impact on the race and championship

Do NOT omit any major crash or retirement mentioned in the supplied data.

# Turning Points
Identify 2–5 moments that fundamentally changed the race outcome and explain why each mattered.

# Strategy Analysis
Analyse tyre choices, pit windows, undercuts, overcuts, Safety Car timing, and which teams gained or lost through strategy.

# Driver & Team Performance
Highlight:
- Driver of the Day candidates
- strongest performances
- biggest disappointments
- midfield battles
- constructors' implications

# By the Numbers
List 3–8 notable statistics such as:
- Fastest Lap
- Largest winning margin
- Closest finish
- Positions gained
- Pit stop times
- Laps led
- Pole margin
- Championship points swings

Writing Guidelines:
- Write approximately 600–850 words.
- Use natural, flowing prose instead of bullet-heavy writing.
- Explain why events mattered, not just what happened.
- Maintain chronological accuracy.
- If multiple sources provide conflicting information, prefer the most authoritative supplied data.
- Never fabricate details. """


def render_story_markdown(story_text: str, race_label: str):
    """Render the story text in a magazine-style article card with a read-aloud button."""
    st.markdown(
        f'<div class="glass-card" style="padding:2rem 2.2rem;line-height:1.7;">',
        unsafe_allow_html=True,
    )
    st.markdown(story_text)
    st.markdown('</div>', unsafe_allow_html=True)

    # Read-aloud via browser SpeechSynthesis — no API key needed, works offline
    safe_text = story_text.replace("##", "").replace("*", "").replace("`", "")
    safe_text_js = (
        safe_text.replace("\\", "\\\\")
                 .replace('"', '\\"')
                 .replace("\n", " ")
                 .replace("</script", "<\\/script")  # defensive: never let AI text break out of the <script> tag
    )

    components.html(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-top:0.8rem;">
      <button id="play-btn" style="
        background:#E10600;color:white;border:none;border-radius:8px;
        padding:8px 16px;font-size:0.82rem;font-weight:600;cursor:pointer;
        display:flex;align-items:center;gap:6px;font-family:Inter,sans-serif;">
        🔊 Read Aloud
      </button>
      <button id="stop-btn" style="
        background:rgba(128,128,128,0.15);color:rgba(160,160,160,0.9);
        border:1px solid rgba(128,128,128,0.25);border-radius:8px;
        padding:8px 16px;font-size:0.82rem;cursor:pointer;display:none;
        font-family:Inter,sans-serif;">
        ⏹ Stop
      </button>
      <span id="status-text" style="font-size:0.75rem;color:rgba(140,140,140,0.8);"></span>
    </div>
    <script>
    (function() {{
      const text = "{safe_text_js}";
      const playBtn = document.getElementById('play-btn');
      const stopBtn = document.getElementById('stop-btn');
      const statusText = document.getElementById('status-text');
      let utterance = null;

      playBtn.onclick = function() {{
        if (!('speechSynthesis' in window)) {{
          statusText.textContent = 'Read-aloud not supported in this browser.';
          return;
        }}
        window.speechSynthesis.cancel();
        utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.onend = function() {{
          playBtn.style.display = 'flex';
          stopBtn.style.display = 'none';
          statusText.textContent = '';
        }};
        window.speechSynthesis.speak(utterance);
        playBtn.style.display = 'none';
        stopBtn.style.display = 'flex';
        statusText.textContent = 'Reading...';
      }};

      stopBtn.onclick = function() {{
        window.speechSynthesis.cancel();
        playBtn.style.display = 'flex';
        stopBtn.style.display = 'none';
        statusText.textContent = '';
      }};
    }})();
    </script>
    """, height=60)


if cached:
    render_story_markdown(cached["story_text"], race_name)

    col_regen, _ = st.columns([1, 3])
    with col_regen:
        if st.button("🔄 Regenerate Story", key="regen_btn"):
            delete_story(season, round_num)
            st.rerun()
else:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:2.4rem;">
        <div style="font-size:2rem;margin-bottom:0.7rem;">📰</div>
        <div style="font-size:0.95rem;color:var(--text-secondary);margin-bottom:1rem;">
            The story for <b style="color:var(--text-primary);">{race_name}</b> hasn't been put together yet.
        </div>
    </div>""", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1, 1, 1])
    with col_btn:
        if st.button("📖 Generate Story", key="gen_btn", type="primary", width="stretch"):
            with st.spinner("Putting together the story for this race…"):
                context = build_race_story_context(season, selected_race)

                if not context["context_text"].strip():
                    st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-secondary);">No race data available yet for this round.</div>', unsafe_allow_html=True)
                    st.stop()

                prompt = (
                    f"Here is the data for the {context['race_name']} "
                    f"({context['date']}):\n\n{context['context_text']}\n\n"
                    f"Write the race weekend recap following the structure in your "
                    f"instructions, using only the facts given above."
                )

                result = generate_text(prompt, system_instruction=SYSTEM_PROMPT, temperature=0.75)

            if result["ok"]:
                save_story(season, round_num, race_name, result["text"])
                st.rerun()
            else:
                st.markdown(
                    f'<div class="glass-card" style="padding:1rem;text-align:center;color:var(--f1-red);">'
                    f'{result["error"]}</div>',
                    unsafe_allow_html=True,
                )

# ── Previously generated stories for this season — card grid ───────────────────
all_cached = list_cached_stories(season)
if len(all_cached) > 1:
    divider()
    st.markdown("""
    <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;
                color:var(--text-secondary);margin-bottom:0.9rem;">📚 All Stories This Season</div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    for i, story in enumerate(all_cached):
        with cols[i % 3]:
            r_name = story.get("race_name", "")
            r_round = story.get("round", "")
            gen_time = datetime.fromtimestamp(story.get("generated_at", 0))
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem 1.1rem;margin-bottom:0.7rem;transition:transform 0.15s;">
                <div style="font-size:0.62rem;color:var(--f1-red);text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:700;">Round {r_round}</div>
                <div style="font-weight:800;font-size:0.98rem;margin:0.3rem 0;">{r_name}</div>
                <div style="font-size:0.68rem;color:var(--text-faint);">
                    📅 {gen_time.strftime('%d %b %Y')}
                </div>
            </div>""", unsafe_allow_html=True)
