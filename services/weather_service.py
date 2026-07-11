"""
F1Intel — Weather Service
Uses Open-Meteo (free, no API key) for circuit weather forecasts.
"""

from __future__ import annotations
import requests
import streamlit as st
from typing import Optional


OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snow", "🌨️"),
    73: ("Moderate snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"),
    81: ("Moderate showers", "🌧️"),
    82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ hail", "⛈️"),
    99: ("Thunderstorm w/ heavy hail", "⛈️"),
}


@st.cache_data(ttl=900, show_spinner=False)
def get_circuit_weather(lat: float, lon: float, days: int = 7) -> dict | None:
    """
    Fetch weather forecast for a circuit location.
    Returns dict with current + daily + hourly data.
    """
    params = {
        "latitude":  lat,
        "longitude": lon,
        "current":   "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,precipitation",
        "daily":     "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "hourly":    "temperature_2m,precipitation_probability,wind_speed_10m",
        "forecast_days": days,
        "timezone":  "auto",
    }
    try:
        r = requests.get(OPEN_METEO_BASE, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_weather_description(code: int) -> tuple[str, str]:
    """Returns (description, emoji) for a WMO weather code."""
    return WMO_CODES.get(code, ("Unknown", "❓"))


def is_wet_conditions(code: int) -> bool:
    """Returns True if weather code indicates wet/rain conditions."""
    return code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}


# Circuit coordinates (used when Jolpica doesn't provide precise coords)
CIRCUIT_COORDS: dict[str, tuple[float, float]] = {
    "bahrain":           (26.0325, 50.5106),
    "jeddah":            (21.6319, 39.1044),
    "albert_park":       (-37.8497, 144.9680),
    "suzuka":            (34.8431, 136.5407),
    "shanghai":          (31.3389, 121.2198),
    "miami":             (25.9581, -80.2389),
    "imola":             (44.3439, 11.7167),
    "monaco":            (43.7347, 7.4206),
    "villeneuve":        (45.5000, -73.5228),
    "catalunya":         (41.5700, 2.2611),
    "red_bull_ring":     (47.2197, 14.7647),
    "silverstone":       (52.0786, -1.0169),
    "hungaroring":       (47.5789, 19.2486),
    "spa":               (50.4372, 5.9714),
    "zandvoort":         (52.3888, 4.5409),
    "monza":             (45.6156, 9.2811),
    "marina_bay":        (1.2914, 103.8640),
    "suzuka":            (34.8431, 136.5407),
    "losail":            (25.4900, 51.4542),
    "americas":          (30.1328, -97.6411),
    "rodriguez":         (19.4042, -99.0907),
    "interlagos":        (-23.7036, -46.6997),
    "las_vegas":         (36.1147, -115.1728),
    "yas_marina":        (24.4672, 54.6031),
    "baku":              (40.3725, 49.8533),
}

def get_circuit_coords(circuit_id: str) -> tuple[float, float] | None:
    key = circuit_id.lower().replace("-", "_")
    return CIRCUIT_COORDS.get(key)
