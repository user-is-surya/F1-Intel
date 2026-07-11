"""
F1Intel — Track Map Component
Renders circuit layout from FastF1 positional data as an SVG/Plotly canvas.
Cars shown as colored dots with driver labels.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.helpers import make_plotly_layout
from utils.theme import get_theme


def _normalize(arr: np.ndarray) -> np.ndarray:
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return arr * 0
    return (arr - mn) / (mx - mn)


def render_track_outline(pos_data: pd.DataFrame, title: str = "Circuit Map") -> go.Figure:
    """
    Build a Plotly figure showing the circuit outline from position data.
    pos_data: DataFrame with X, Y columns.
    """
    fig = go.Figure()
    from config.settings import get_theme_plotly
    _p = get_theme_plotly(get_theme())

    if pos_data.empty or "X" not in pos_data.columns or "Y" not in pos_data.columns:
        fig.add_annotation(text="No track data", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color=_p["font"]))
        return fig

    x = pos_data["X"].values
    y = pos_data["Y"].values

    # Track outline (thick semi-transparent line)
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color="rgba(128,128,128,0.27)", width=16),
        showlegend=False, hoverinfo="skip",
    ))

    # Racing surface (thin bright line)
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color="rgba(128,128,128,0.9)", width=3),
        showlegend=False, hoverinfo="skip",
        name="Track",
    ))

    fig.update_layout(
        paper_bgcolor=_p["paper_bg"],
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, scaleanchor="y"),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500,
        title=dict(text=title, font=dict(color=_p["font"], size=13)),
    )
    return fig


def add_driver_dots(fig: go.Figure, driver_positions: list[dict],
                    track_x_range: tuple, track_y_range: tuple) -> go.Figure:
    """
    Overlay driver position dots onto a track map figure.
    driver_positions: list of {name, x, y, color, number}
    """
    for dp in driver_positions:
        x      = dp.get("x", 0)
        y      = dp.get("y", 0)
        color  = dp.get("color", "#E10600")
        name   = dp.get("name", "")
        number = dp.get("number", "")

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(
                color=color,
                size=14,
                line=dict(color="white", width=2),
                symbol="circle",
            ),
            text=[str(number)],
            textfont=dict(size=8, color="white"),
            textposition="middle center",
            name=name,
            hovertemplate=f"<b>{name}</b><br>#{number}<extra></extra>",
            showlegend=True,
        ))

    return fig


def render_track_map_from_session(session, driver_list: list[str],
                                   color_map: dict[str, str]) -> None:
    """
    Render a track map from a FastF1 session's fastest lap position data.
    Falls back to circuit reference lap if driver positions unavailable.
    """
    if session is None:
        st.info("No session loaded for track map.")
        return

    try:
        # Get circuit outline from first available driver
        from services.fastf1_service import get_fastest_lap, get_pos_data
        circuit_fig = None

        for driver in driver_list[:1]:
            lap = get_fastest_lap(session, driver)
            if lap is not None:
                pos = get_pos_data(lap)
                if not pos.empty:
                    circuit_fig = render_track_outline(pos, title="Track Map")
                    break

        if circuit_fig is None:
            st.info("Track position data not available for this session.")
            return

        # Get current (end-of-lap) positions for all drivers
        from services.fastf1_service import get_driver_info_ff1, get_fastest_lap, get_pos_data
        driver_dots = []

        for driver in driver_list:
            try:
                lap  = get_fastest_lap(session, driver)
                if lap is None:
                    continue
                pos  = get_pos_data(lap)
                if pos.empty or "X" not in pos.columns:
                    continue
                info = get_driver_info_ff1(session, driver)
                # Use the final position (end of lap)
                final = pos.iloc[-1]
                driver_dots.append({
                    "name":   driver,
                    "number": info.get("number", ""),
                    "x":      final["X"],
                    "y":      final["Y"],
                    "color":  color_map.get(driver, "#E10600"),
                })
            except Exception:
                continue

        if driver_dots:
            # Compute x/y ranges from first trace
            x_vals = circuit_fig.data[0].x
            y_vals = circuit_fig.data[0].y
            circuit_fig = add_driver_dots(
                circuit_fig, driver_dots,
                (min(x_vals), max(x_vals)),
                (min(y_vals), max(y_vals)),
            )

        st.plotly_chart(circuit_fig, width='stretch')

    except Exception as e:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-muted);">Track position data not available for this session.</div>', unsafe_allow_html=True)


def render_animated_track_map(session, driver: str, color: str = "#E10600") -> None:
    """
    Render an animated lap replay for a single driver using position data.
    """
    if session is None:
        return

    from config.settings import get_theme_plotly
    _p = get_theme_plotly(get_theme())

    try:
        from services.fastf1_service import get_fastest_lap, get_pos_data
        lap = get_fastest_lap(session, driver)
        if lap is None:
            st.info("No fastest lap for animation.")
            return

        pos = get_pos_data(lap)
        if pos.empty or "X" not in pos.columns:
            st.info("Position data not available.")
            return

        # Downsample for performance
        step = max(1, len(pos) // 200)
        pos  = pos.iloc[::step].reset_index(drop=True)

        x_all = pos["X"].values
        y_all = pos["Y"].values

        frames = []
        for i in range(1, len(x_all)):
            frames.append(go.Frame(
                data=[
                    go.Scatter(x=x_all[:i], y=y_all[:i],
                               mode="lines", line=dict(color=color, width=2)),
                    go.Scatter(x=[x_all[i]], y=[y_all[i]],
                               mode="markers", marker=dict(color=color, size=12,
                               line=dict(color="white", width=2))),
                ],
                name=str(i),
            ))

        fig = go.Figure(
            data=[
                go.Scatter(x=x_all, y=y_all, mode="lines",
                           line=dict(color="rgba(128,128,128,0.27)", width=14), showlegend=False),
                go.Scatter(x=x_all[:1], y=y_all[:1], mode="lines",
                           line=dict(color=color, width=2), showlegend=False),
                go.Scatter(x=[x_all[0]], y=[y_all[0]], mode="markers",
                           marker=dict(color=color, size=12), showlegend=False),
            ],
            frames=frames,
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False, scaleanchor="y"),
            yaxis=dict(visible=False),
            height=500,
            title=dict(text=f"{driver} — Lap Animation", font=dict(color=_p["font"])),
            updatemenus=[dict(
                type="buttons", showactive=False,
                y=0, x=0.5, xanchor="center",
                buttons=[
                    dict(label="▶ Play",  method="animate",
                         args=[None, {"frame": {"duration": 30}, "fromcurrent": True}]),
                    dict(label="⏸ Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
                ],
            )],
        )
        st.plotly_chart(fig, width='stretch')

    except Exception as e:
        st.markdown('<div class="glass-card" style="padding:1rem;text-align:center;color:var(--text-muted);">Animation data not available for this driver.</div>', unsafe_allow_html=True)
