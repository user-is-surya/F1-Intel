"""
F1Intel — Race Countdown & Session Schedule
- Countdown timer via components.html (JS-safe)
- Schedule times shown in user's LOCAL timezone via JS
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz
from utils.flags import get_flag
from utils.theme import get_theme
from config.settings import get_theme_css_vars


def render_countdown(race: dict | None) -> None:
    if not race:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:2rem;">
            <div style="color:var(--text-muted);">No upcoming race scheduled.</div>
        </div>""", unsafe_allow_html=True)
        return

    # components.html() renders into its own <iframe> — a separate document
    # that can't see the main page's `:root` CSS variables. So this widget
    # needs literal color values, resolved here in Python for whichever
    # theme is currently active, rather than var(--...) references.
    c = get_theme_css_vars(get_theme())

    race_name = race.get("raceName", "Next Race")
    circuit   = race.get("Circuit", {}).get("circuitName", "")
    country   = race.get("Circuit", {}).get("Location", {}).get("country", "")
    date_str  = race.get("date", "")
    time_str  = race.get("time", "12:00:00Z")
    round_num = race.get("round", "?")
    flag      = get_flag(country)

    try:
        race_dt_iso = f"{date_str}T{time_str.rstrip('Z')}+00:00"
        datetime.fromisoformat(race_dt_iso)  # validate
    except Exception:
        race_dt_iso = ""

    st.markdown(f"""
    <div class="glass-card fade-in" style="text-align:center;padding:1.2rem 1rem 0.5rem;">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.14em;color:var(--text-muted);margin-bottom:0.4rem;">
            ⏱ ROUND {round_num} · NEXT RACE
        </div>
        <div style="font-size:1.25rem;font-weight:800;margin-bottom:0.15rem;">
            {flag} {race_name}
        </div>
        <div style="font-size:0.78rem;color:var(--text-muted);">
            {circuit} · {country}
        </div>
    </div>""", unsafe_allow_html=True)

    components.html(f"""<!DOCTYPE html>
<html><head>
<style>
body{{margin:0;background:transparent;font-family:Inter,sans-serif;}}
.row{{display:flex;justify-content:center;gap:10px;padding:12px 0 8px;}}
.block{{background:{c['--overlay-soft']};border:1px solid {c['--divider-soft']};
        border-radius:10px;padding:9px 14px;text-align:center;min-width:60px;}}
.num{{font-size:1.9rem;font-weight:800;color:#E10600;
      font-family:'Courier New',monospace;line-height:1;}}
.unit{{font-size:0.58rem;text-transform:uppercase;letter-spacing:0.12em;
       color:{c['--text-muted']};margin-top:2px;}}
</style></head><body>
<div class="row">
  <div class="block"><div class="num" id="d">--</div><div class="unit">Days</div></div>
  <div class="block"><div class="num" id="h">--</div><div class="unit">Hours</div></div>
  <div class="block"><div class="num" id="m">--</div><div class="unit">Mins</div></div>
  <div class="block"><div class="num" id="s">--</div><div class="unit">Secs</div></div>
</div>
<script>
const target = new Date("{race_dt_iso}");
function update(){{
  const diff = target - new Date();
  if(diff<=0){{['d','h','m','s'].forEach(id=>document.getElementById(id).textContent='00');return;}}
  const f=n=>String(Math.floor(n)).padStart(2,'0');
  document.getElementById('d').textContent=f(diff/86400000);
  document.getElementById('h').textContent=f((diff%86400000)/3600000);
  document.getElementById('m').textContent=f((diff%3600000)/60000);
  document.getElementById('s').textContent=f((diff%60000)/1000);
}}
update(); setInterval(update,1000);
</script></body></html>""", height=105, scrolling=False)


def render_session_schedule(race: dict | None) -> None:
    if not race:
        return

    # Same iframe/CSS-variable limitation as render_countdown above.
    c = get_theme_css_vars(get_theme())

    sessions = []
    for key, label in [
        ("FirstPractice",    "FP1"),
        ("SecondPractice",   "FP2"),
        ("ThirdPractice",    "FP3"),
        ("Qualifying",       "Qualifying"),
        ("Sprint",           "Sprint"),
        ("SprintQualifying", "Sprint Qualifying"),
    ]:
        s = race.get(key)
        if s and s.get("date"):
            sessions.append((label, s.get("date",""), s.get("time","")))
    sessions.append(("Race", race.get("date",""), race.get("time","")))

    now    = datetime.now(pytz.UTC)
    # Build session data as JSON for JS to render with local timezone
    import json
    sess_data = []
    for label, date, time_s in sessions:
        if not date:
            continue
        try:
            iso = f"{date}T{time_s.rstrip('Z')}+00:00"
            dt  = datetime.fromisoformat(iso)
            is_past = dt < now
        except Exception:
            iso     = ""
            is_past = False
        sess_data.append({
            "label":   label,
            "iso":     iso,
            "is_past": is_past,
            "is_race": label == "Race",
        })

    # Render via components.html so JS can do timezone conversion
    components.html(f"""<!DOCTYPE html>
<html><head>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:Inter,sans-serif;background:{c['--overlay-soft']};
     border:1px solid {c['--divider-soft']};border-radius:14px;padding:12px 14px;
     color:{c['--text-primary']};}}
.hdr{{font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;
      color:{c['--text-muted']};margin-bottom:8px;}}
.row{{display:flex;justify-content:space-between;align-items:center;
      padding:6px 0;border-bottom:1px solid {c['--divider-soft']};}}
.row:last-child{{border-bottom:none;}}
.label{{font-size:0.82rem;font-weight:600;color:{c['--text-primary']};}}
.time{{font-size:0.72rem;color:{c['--text-muted']};font-family:'Courier New',monospace;}}
.past{{opacity:0.4;}}
.race-label{{color:#E10600;}}
.tz-note{{font-size:0.58rem;color:{c['--text-faint']};margin-top:8px;text-align:right;}}
</style></head>
<body>
<div class="hdr">📅 WEEKEND SCHEDULE</div>
<div id="rows"></div>
<div class="tz-note" id="tz-note">UTC</div>
<script>
const sessions = {json.dumps(sess_data)};
function render() {{
  const tz  = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const tzS = tz.replace('_',' ');
  document.getElementById('tz-note').textContent = tzS;
  const fmt = new Intl.DateTimeFormat('en-GB', {{
    weekday:'short', day:'2-digit', month:'short',
    hour:'2-digit', minute:'2-digit', hour12:false, timeZone: tz
  }});
  let html = '';
  sessions.forEach(function(s) {{
    const timeStr = s.iso ? fmt.format(new Date(s.iso)) : '—';
    const pastCls = s.is_past ? ' past' : '';
    const lblCls  = s.is_race ? ' race-label' : '';
    html += '<div class="row' + pastCls + '"><span class="label' + lblCls + '">' +
            s.label + '</span><span class="time">' + timeStr + '</span></div>';
  }});
  document.getElementById('rows').innerHTML = html;
}}
render();
</script>
</body></html>""", height=int(len(sess_data) * 36 + 70), scrolling=False)
