"""
F1Intel — Telemetry Chart Components
Speed, throttle, brake, RPM, gear, DRS, delta time charts.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.helpers import make_plotly_layout


def render_speed_trace(tel1: pd.DataFrame, tel2: pd.DataFrame,
                        driver1: str, driver2: str,
                        color1: str = "#E10600", color2: str = "#00D2BE") -> None:
    """Render side-by-side speed trace comparison."""
    if tel1.empty and tel2.empty:
        st.info("No telemetry data available.")
        return

    fig = go.Figure()

    if not tel1.empty and "Speed" in tel1.columns and "Distance" in tel1.columns:
        fig.add_trace(go.Scatter(
            x=tel1["Distance"], y=tel1["Speed"],
            name=driver1, line=dict(color=color1, width=2),
            hovertemplate=f"<b>{driver1}</b><br>Distance: %{{x:.0f}}m<br>Speed: %{{y:.0f}} km/h<extra></extra>"
        ))

    if not tel2.empty and "Speed" in tel2.columns and "Distance" in tel2.columns:
        fig.add_trace(go.Scatter(
            x=tel2["Distance"], y=tel2["Speed"],
            name=driver2, line=dict(color=color2, width=2),
            hovertemplate=f"<b>{driver2}</b><br>Distance: %{{x:.0f}}m<br>Speed: %{{y:.0f}} km/h<extra></extra>"
        ))

    layout = make_plotly_layout(f"Speed Trace — {driver1} vs {driver2}", height=300)
    layout["xaxis"]["title"] = "Distance (m)"
    layout["yaxis"]["title"] = "Speed (km/h)"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')


def render_telemetry_comparison(tel1: pd.DataFrame, tel2: pd.DataFrame,
                                  driver1: str, driver2: str,
                                  color1: str = "#E10600", color2: str = "#00D2BE") -> None:
    """
    Render a full multi-panel telemetry comparison:
    Speed / Throttle / Brake / RPM / Gear / DRS
    """
    if tel1.empty and tel2.empty:
        st.info("No telemetry data to display.")
        return

    panels = [
        ("Speed",    "km/h",   False),
        ("Throttle", "%",      False),
        ("Brake",    "",       False),
        ("RPM",      "RPM",    False),
        ("nGear",    "Gear",   True),
        ("DRS",      "DRS",    True),
    ]

    # Only include panels where at least one driver has data
    available = []
    for col, unit, is_step in panels:
        has1 = not tel1.empty and col in tel1.columns
        has2 = not tel2.empty and col in tel2.columns
        if has1 or has2:
            available.append((col, unit, is_step, has1, has2))

    if not available:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-muted);">Telemetry channels not available.</div>', unsafe_allow_html=True)
        return

    n = len(available)
    fig = make_subplots(
        rows=n, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=[a[0] for a in available],
    )

    from config.settings import get_theme_plotly
    from utils.theme import get_theme
    _p = get_theme_plotly(get_theme())
    PLOTLY_GRID, PLOTLY_FONT_CLR = _p["grid"], _p["font"]
    PLOTLY_PAPER_BG, PLOTLY_PLOT_BG = _p["paper_bg"], _p["plot_bg"]

    for i, (col, unit, is_step, has1, has2) in enumerate(available, start=1):
        line_shape = "hv" if is_step else "linear"

        if has1:
            fig.add_trace(go.Scatter(
                x=tel1["Distance"] if "Distance" in tel1.columns else tel1.index,
                y=tel1[col],
                name=driver1 if i == 1 else None,
                showlegend=(i == 1),
                line=dict(color=color1, width=1.5, shape=line_shape),
                hovertemplate=f"<b>{driver1}</b> {col}: %{{y}}<extra></extra>",
            ), row=i, col=1)

        if has2:
            fig.add_trace(go.Scatter(
                x=tel2["Distance"] if "Distance" in tel2.columns else tel2.index,
                y=tel2[col],
                name=driver2 if i == 1 else None,
                showlegend=(i == 1),
                line=dict(color=color2, width=1.5, shape=line_shape),
                hovertemplate=f"<b>{driver2}</b> {col}: %{{y}}<extra></extra>",
            ), row=i, col=1)

        fig.update_yaxes(
            title_text=unit if unit else col, row=i, col=1,
            gridcolor=PLOTLY_GRID, linecolor=PLOTLY_GRID,
            title_font=dict(size=10, color=PLOTLY_FONT_CLR),
        )

    fig.update_xaxes(
        title_text="Distance (m)", row=n, col=1,
        gridcolor=PLOTLY_GRID, linecolor=PLOTLY_GRID,
    )

    fig.update_layout(
        paper_bgcolor=PLOTLY_PAPER_BG,
        plot_bgcolor=PLOTLY_PLOT_BG,
        font=dict(color=PLOTLY_FONT_CLR, family="Inter, sans-serif"),
        height=130 * n,
        margin=dict(l=50, r=20, t=30, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=PLOTLY_FONT_CLR),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor=_p["hover_bg"], font=dict(color=_p["hover_font"])),
    )

    st.plotly_chart(fig, width='stretch')


def render_delta_time(tel1: pd.DataFrame, tel2: pd.DataFrame,
                       driver1: str, driver2: str,
                       color1: str = "#E10600", color2: str = "#00D2BE") -> None:
    """Render delta time chart (positive = driver1 ahead)."""
    if tel1.empty or tel2.empty:
        st.info("Delta time requires telemetry for both drivers.")
        return
    if "Distance" not in tel1.columns or "Distance" not in tel2.columns:
        st.info("Distance data not available for delta calculation.")
        return

    try:
        # Interpolate both onto common distance axis
        import numpy as np
        d_min = max(tel1["Distance"].min(), tel2["Distance"].min())
        d_max = min(tel1["Distance"].max(), tel2["Distance"].max())
        common_dist = np.linspace(d_min, d_max, 500)

        # We need timestamps to compute delta — use Time channel if available
        if "Time" not in tel1.columns or "Time" not in tel2.columns:
            st.info("Time channel not available for delta calculation.")
            return

        t1 = tel1["Time"].dt.total_seconds() if hasattr(tel1["Time"], "dt") else tel1["Time"]
        t2 = tel2["Time"].dt.total_seconds() if hasattr(tel2["Time"], "dt") else tel2["Time"]

        t1_interp = np.interp(common_dist, tel1["Distance"].values, t1.values)
        t2_interp = np.interp(common_dist, tel2["Distance"].values, t2.values)
        delta = t1_interp - t2_interp

        fig = go.Figure()
        fig.add_hline(y=0, line_color="rgba(128,128,128,0.36)", line_width=1)
        fig.add_trace(go.Scatter(
            x=common_dist, y=delta,
            fill="tozeroy",
            line=dict(color=color1, width=2),
            name=f"Δ {driver1} vs {driver2}",
            hovertemplate="Distance: %{x:.0f}m<br>Delta: %{y:.3f}s<extra></extra>",
        ))

        layout = make_plotly_layout(f"Delta Time — {driver1} vs {driver2}", height=250)
        layout["xaxis"]["title"] = "Distance (m)"
        layout["yaxis"]["title"] = f"Delta (s) — + favours {driver1}"
        layout["yaxis"]["zeroline"] = True
        layout["yaxis"]["zerolinecolor"] = "var(--text-muted)"
        fig.update_layout(**layout)
        st.plotly_chart(fig, width='stretch')

    except Exception as e:
        st.info("Delta time requires matching distance data for both drivers.")


def render_racing_lines(pos1: pd.DataFrame, pos2: pd.DataFrame,
                         driver1: str, driver2: str,
                         color1: str = "#E10600", color2: str = "#00D2BE") -> None:
    """Render X/Y racing line overlay for two drivers."""
    if pos1.empty and pos2.empty:
        return

    fig = go.Figure()

    for pos_data, driver, color in [(pos1, driver1, color1), (pos2, driver2, color2)]:
        if pos_data.empty:
            continue
        if "X" in pos_data.columns and "Y" in pos_data.columns:
            fig.add_trace(go.Scatter(
                x=pos_data["X"], y=pos_data["Y"],
                mode="lines",
                name=driver,
                line=dict(color=color, width=2),
            ))

    layout = make_plotly_layout("Racing Line Comparison", height=450)
    layout["xaxis"]["showgrid"] = False
    layout["yaxis"]["showgrid"] = False
    layout["xaxis"]["visible"]  = False
    layout["yaxis"]["visible"]  = False
    layout["yaxis"]["scaleanchor"] = "x"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')
