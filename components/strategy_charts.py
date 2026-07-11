"""
F1Intel — Strategy Chart Components
Tire stints, degradation, pit windows, strategy timelines.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config.settings import TIRE_COLORS
from utils.helpers import make_plotly_layout
from utils.formatters import format_laptime


def render_strategy_timeline(stints: pd.DataFrame, total_laps: int = 70) -> None:
    """
    Render Gantt-style strategy timeline showing tire stints per driver.
    stints: DataFrame with columns [Driver, Stint, Compound, first_lap, last_lap, laps]
    """
    if stints.empty:
        st.info("No stint data available.")
        return

    drivers = stints["Driver"].unique().tolist()
    fig = go.Figure()

    for driver in drivers:
        driver_stints = stints[stints["Driver"] == driver]
        for _, row in driver_stints.iterrows():
            compound   = str(row.get("Compound", "UNKNOWN")).upper()
            color      = TIRE_COLORS.get(compound, "#888888")
            first_lap  = int(row.get("first_lap", 1))
            last_lap   = int(row.get("last_lap", first_lap))
            laps_count = int(row.get("laps", last_lap - first_lap + 1))

            fig.add_trace(go.Bar(
                x=[laps_count],
                y=[driver],
                orientation="h",
                base=[first_lap - 1],
                marker=dict(color=color, line=dict(color="rgba(0,0,0,0.4)", width=1)),
                name=compound,
                showlegend=False,
                hovertemplate=(
                    f"<b>{driver}</b><br>"
                    f"Compound: {compound}<br>"
                    f"Laps {first_lap}–{last_lap} ({laps_count} laps)<extra></extra>"
                ),
                width=0.6,
            ))

    # Compound legend
    for compound, color in TIRE_COLORS.items():
        if compound in ["UNKNOWN", "TEST_UNKNOWN"]:
            continue
        fig.add_trace(go.Bar(
            x=[0], y=[""], orientation="h",
            name=compound, marker_color=color,
            showlegend=True, visible="legendonly",
        ))

    layout = make_plotly_layout("Race Strategy — Tire Stints", height=max(350, len(drivers) * 40))
    layout["xaxis"]["title"]  = "Lap"
    layout["xaxis"]["range"]  = [0, total_laps]
    layout["barmode"]         = "stack"
    layout["bargap"]          = 0.15
    layout["legend"]          = {
        "bgcolor": "rgba(0,0,0,0)", "orientation": "h",
        "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1,
    }
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')


def render_lap_time_evolution(laps: pd.DataFrame, drivers: list[str],
                               color_map: dict[str, str]) -> None:
    """Plot lap time evolution for selected drivers over a race."""
    if laps.empty:
        st.info("No lap data available.")
        return

    fig = go.Figure()

    for driver in drivers:
        driver_laps = laps[laps["Driver"] == driver].copy()
        if driver_laps.empty:
            continue

        # Convert LapTime to seconds
        if "LapTime" in driver_laps.columns:
            driver_laps["LapSec"] = driver_laps["LapTime"].dt.total_seconds()
            driver_laps = driver_laps.dropna(subset=["LapSec"])
            # Filter out outliers (pit laps, SC laps) - keep within 110% of median
            median = driver_laps["LapSec"].median()
            driver_laps = driver_laps[driver_laps["LapSec"] < median * 1.15]

            color = color_map.get(driver, "#888888")
            fig.add_trace(go.Scatter(
                x=driver_laps["LapNumber"],
                y=driver_laps["LapSec"],
                name=driver,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=4),
                hovertemplate=(
                    f"<b>{driver}</b><br>Lap %{{x}}<br>"
                    "Time: %{customdata}<extra></extra>"
                ),
                customdata=[format_laptime(s) for s in driver_laps["LapSec"]],
            ))

    layout = make_plotly_layout("Lap Time Evolution", height=380)
    layout["xaxis"]["title"] = "Lap Number"
    layout["yaxis"]["title"] = "Lap Time (s)"
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')


def render_tire_degradation(laps: pd.DataFrame, driver: str,
                              color_map: dict[str, str] | None = None) -> None:
    """Show per-compound tire degradation for a single driver."""
    if laps.empty:
        return

    driver_laps = laps[laps["Driver"] == driver].copy()
    if driver_laps.empty:
        st.info(f"No laps found for {driver}.")
        return

    if "LapTime" not in driver_laps.columns or "TyreLife" not in driver_laps.columns:
        st.info("Tire life data not available.")
        return

    driver_laps["LapSec"] = driver_laps["LapTime"].dt.total_seconds()
    driver_laps = driver_laps.dropna(subset=["LapSec", "TyreLife", "Compound"])
    median = driver_laps["LapSec"].median()
    driver_laps = driver_laps[driver_laps["LapSec"] < median * 1.12]

    fig = go.Figure()

    for compound in driver_laps["Compound"].unique():
        c_laps = driver_laps[driver_laps["Compound"] == compound]
        color  = TIRE_COLORS.get(str(compound).upper(), "#888888")
        fig.add_trace(go.Scatter(
            x=c_laps["TyreLife"],
            y=c_laps["LapSec"],
            name=compound,
            mode="markers+lines",
            line=dict(color=color, width=2),
            marker=dict(color=color, size=5),
            hovertemplate=f"Tire age: %{{x}} laps<br>Lap: %{{y:.3f}}s<extra>{compound}</extra>",
        ))

    layout = make_plotly_layout(f"{driver} — Tire Degradation", height=320)
    layout["xaxis"]["title"] = "Tire Age (laps)"
    layout["yaxis"]["title"] = "Lap Time (s)"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')


def render_pit_stop_summary(pit_stops: list[dict]) -> None:
    """Render pit stop summary bar chart."""
    if not pit_stops:
        st.info("No pit stop data.")
        return

    import pandas as pd
    df = pd.DataFrame(pit_stops)

    if "duration" not in df.columns or "driverId" not in df.columns:
        st.info("Pit stop data format not compatible.")
        return

    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df = df.dropna(subset=["duration"])
    df = df[df["duration"] < 60]  # remove outliers

    fig = go.Figure()
    for _, row in df.iterrows():
        driver_id = row.get("driverId", "")
        lap       = row.get("lap", "?")
        duration  = float(row.get("duration", 0))
        color = "#E10600" if duration < 3.0 else ("#FFD700" if duration < 4.0 else "#888888")
        fig.add_trace(go.Bar(
            x=[driver_id],
            y=[duration],
            name=f"Lap {lap}",
            marker_color=color,
            hovertemplate=f"<b>{driver_id}</b><br>Lap {lap}: {duration:.3f}s<extra></extra>",
            showlegend=False,
        ))

    layout = make_plotly_layout("Pit Stop Durations", height=320)
    layout["xaxis"]["title"] = "Driver"
    layout["yaxis"]["title"] = "Duration (s)"
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width='stretch')
