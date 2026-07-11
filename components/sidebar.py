"""
F1Intel — Branded Sidebar
Uppercase labels, always collapsible, clean minimal design.
"""

from __future__ import annotations
import streamlit as st
import os
from config.settings import APP_VERSION, CURRENT_SEASON
from utils.helpers import get_asset_path
from utils.theme import render_theme_toggle


def render_sidebar() -> int:
    """Render the F1Intel branded sidebar. Returns selected season."""
    with st.sidebar:
        # ── Logo / Brand ──────────────────────────────────────────
        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)
        else:
            st.markdown("""
            <div style="padding:0.6rem 0 0.4rem;">
                <span style="font-size:2.2rem;font-weight:900;letter-spacing:-0.04em;
                             background:linear-gradient(90deg,#E10600,#FF4444);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                    F1</span><span style="font-size:2.2rem;font-weight:900;
                             color:var(--text-primary);letter-spacing:-0.04em;">Intel</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            '<p style="font-size:0.62rem;color:var(--text-muted);'
            'text-transform:uppercase;letter-spacing:0.18em;margin-top:-0.3rem;'
            'margin-bottom:0.8rem;">FORMULA 1 INTELLIGENCE</p>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<hr style="border:none;border-top:1px solid var(--divider-soft);margin:0 0 0.8rem;">',
            unsafe_allow_html=True,
        )

        # ── Season selector ────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.6rem;color:var(--text-muted);'
            'text-transform:uppercase;letter-spacing:0.16em;margin-bottom:0.25rem;">SEASON</p>',
            unsafe_allow_html=True,
        )
        season = st.selectbox(
            "Season",
            options=list(range(CURRENT_SEASON, 2017, -1)),
            index=0,
            label_visibility="collapsed",
            key="global_season",
        )
        st.session_state["selected_season"] = season

        st.markdown(
            '<hr style="border:none;border-top:1px solid var(--divider-soft);margin:0.8rem 0 0.4rem;">',
            unsafe_allow_html=True,
        )

        # ── Navigation label (Streamlit renders the links automatically above this) ──
        st.markdown(
            '<p style="font-size:0.6rem;color:var(--text-muted);'
            'text-transform:uppercase;letter-spacing:0.16em;margin-bottom:0.3rem;">NAVIGATION</p>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<hr style="border:none;border-top:1px solid var(--divider-soft);margin:0.4rem 0 0.6rem;">',
            unsafe_allow_html=True,
        )

        # ── Appearance ────────────────────────────────────────────
        render_theme_toggle()

        # ── Footer ────────────────────────────────────────────────
        st.markdown(f"""
        <div style="text-align:center;padding:0.6rem 0 0.2rem;">
            <p style="font-size:0.58rem;color:var(--text-faint);margin:0;
                      text-transform:uppercase;letter-spacing:0.1em;">
                F1INTEL v{APP_VERSION} · {season}
            </p>
        </div>
        """, unsafe_allow_html=True)

    return season
