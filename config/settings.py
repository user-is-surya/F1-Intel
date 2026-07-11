"""
F1Intel — Application Settings
Dynamic season detection + API configuration
"""

from datetime import datetime
import pytz

# ── Season ─────────────────────────────────────────────
def get_current_season() -> int:
    """Return the active F1 season year. Adjusts to next year after November."""
    now = datetime.now(pytz.UTC)
    # F1 season typically runs March → November/December
    # If we're in Dec, season is still current year
    return now.year

CURRENT_SEASON: int = get_current_season()

# Earliest season with full Jolpica data
MIN_SEASON: int = 1950
# Earliest season FastF1 telemetry is reliable
FASTF1_MIN_SEASON: int = 2018

# ── API Endpoints ───────────────────────────────────────
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
OPENF1_BASE  = "https://api.openf1.org/v1"

# ── HTTP tuning (performance) ───────────────────────────
# Shared, tighter timeouts + small retry budget. The old code opened a
# fresh connection per request with a 12s timeout and no retries, which
# is a big reason pages "took forever" — one slow/flaky upstream call
# stalled the whole page. See services/http_client.py.
HTTP_TIMEOUT        = 6      # seconds
HTTP_TOTAL_RETRIES  = 2
HTTP_BACKOFF        = 0.3    # seconds, exponential backoff factor

# ── Cache TTL (seconds) ─────────────────────────────────
CACHE_TTL = {
    "standings":    300,     # 5 min — changes after each race
    "schedule":     3600,    # 1 hr  — rarely changes
    "results":      600,     # 10 min
    "driver_info":  86400,   # 1 day
    "constructor":  86400,
    "circuit":      86400,
    "live_timing":  5,       # 5 sec — nearly real-time
    "telemetry":    3600,    # 1 hr  — session data
    "weather":      900,     # 15 min
}

# ── FastF1 cache directory ──────────────────────────────
import os
FASTF1_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")
os.makedirs(FASTF1_CACHE_DIR, exist_ok=True)

# ── App metadata ────────────────────────────────────────
APP_NAME    = "F1Intel"
APP_TAGLINE = "Formula 1 Intelligence Platform"
APP_VERSION = "3.0.0"

# ── Contact / funding ────────────────────────────────────
CONTACT_EMAIL = "bdotsurya@gmail.com"

# ── Tire compound colors ────────────────────────────────
TIRE_COLORS = {
    "SOFT":   "#E8002D",
    "MEDIUM": "#FFF200",
    "HARD":   "#FFFFFF",
    "INTER":  "#43B02A",
    "WET":    "#0067FF",
    "UNKNOWN": "#888888",
    "TEST_UNKNOWN": "#888888",
}

# ── Session type labels ─────────────────────────────────
SESSION_LABELS = {
    "FP1":         "Practice 1",
    "FP2":         "Practice 2",
    "FP3":         "Practice 3",
    "Q":           "Qualifying",
    "SQ":          "Sprint Qualifying",
    "S":           "Sprint",
    "R":           "Race",
    "Qualifying":  "Qualifying",
    "Race":        "Race",
    "Sprint":      "Sprint",
    "Practice 1":  "Practice 1",
    "Practice 2":  "Practice 2",
    "Practice 3":  "Practice 3",
}

# ── Number of results per page for tables ──────────────
PAGE_SIZE = 25

# ══════════════════════════════════════════════════════════════════════════
# THEME SYSTEM — single source of truth for both the injected CSS variables
# and Plotly chart colors (Plotly can't read CSS variables, so it needs its
# own literal values, kept in sync with the CSS palette right here).
# ══════════════════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "css": {
            "--f1-red":        "#E10600",
            "--f1-red-dark":   "#B80500",
            "--f1-gold":       "#FFD700",
            "--f1-silver":     "#C0C0C0",
            "--f1-bronze":     "#CD7F32",
            "--bg-primary":    "#0A0A0F",
            "--bg-secondary":  "#13131A",
            "--bg-card":       "rgba(255,255,255,0.045)",
            "--bg-card-hover": "rgba(255,255,255,0.075)",
            "--bg-card-solid": "#14141C",
            "--glass-border":  "rgba(255,255,255,0.09)",
            "--glass-accent":  "rgba(225,6,0,0.4)",
            "--divider-soft":  "rgba(255,255,255,0.07)",
            "--overlay-soft":  "rgba(255,255,255,0.045)",
            "--text-primary":  "#F5F6F8",
            "--text-secondary":"rgba(245,246,248,0.62)",
            "--text-muted":    "rgba(245,246,248,0.40)",
            "--text-faint":    "rgba(245,246,248,0.24)",
            "--chrome-text-primary":   "#F5F6F8",
            "--chrome-text-secondary": "rgba(245,246,248,0.62)",
            "--grid-color":    "rgba(255,255,255,0.07)",
            "--glow-red":      "0 0 30px rgba(225,6,0,0.28)",
            "--shadow-card":   "0 12px 40px rgba(0,0,0,0.45)",
            "--scrollbar-thumb": "rgba(255,255,255,0.15)",
        },
        "plotly": {
            "paper_bg": "rgba(0,0,0,0)",
            "plot_bg":  "rgba(255,255,255,0.02)",
            "grid":     "rgba(255,255,255,0.09)",
            "font":     "#E8E9EC",
            "muted":    "rgba(232,233,236,0.5)",
            "hover_bg": "#1A1A24",
            "hover_font": "#FFFFFF",
        },
    },
    "light": {
        "css": {
            "--f1-red":        "#E10600",
            "--f1-red-dark":   "#B80500",
            "--f1-gold":       "#C9971F",
            "--f1-silver":     "#8B8F98",
            "--f1-bronze":     "#A9662E",
            "--bg-primary":    "#F2F3F6",
            "--bg-secondary":  "#FFFFFF",
            "--bg-card":       "rgba(16,18,24,0.035)",
            "--bg-card-hover": "rgba(16,18,24,0.06)",
            "--bg-card-solid": "#FFFFFF",
            "--glass-border":  "rgba(16,18,24,0.10)",
            "--glass-accent":  "rgba(225,6,0,0.35)",
            "--divider-soft":  "rgba(16,18,24,0.09)",
            "--overlay-soft":  "rgba(16,18,24,0.045)",
            "--text-primary":  "#14161C",
            "--text-secondary":"rgba(20,22,28,0.68)",
            "--text-muted":    "rgba(20,22,28,0.48)",
            "--text-faint":    "rgba(20,22,28,0.30)",
            "--chrome-text-primary":   "#14161C",
            "--chrome-text-secondary": "rgba(20,22,28,0.68)",
            "--grid-color":    "rgba(16,18,24,0.10)",
            "--glow-red":      "0 0 22px rgba(225,6,0,0.18)",
            "--shadow-card":   "0 10px 28px rgba(20,22,28,0.10)",
            "--scrollbar-thumb": "rgba(16,18,24,0.18)",
        },
        "plotly": {
            "paper_bg": "rgba(0,0,0,0)",
            "plot_bg":  "rgba(16,18,24,0.02)",
            "grid":     "rgba(16,18,24,0.12)",
            "font":     "#20232B",
            "muted":    "rgba(32,35,43,0.55)",
            "hover_bg": "#FFFFFF",
            "hover_font": "#14161C",
        },
    },
}


def get_theme_css_vars(theme: str) -> dict:
    return THEMES.get(theme, THEMES["dark"])["css"]


def get_theme_plotly(theme: str) -> dict:
    return THEMES.get(theme, THEMES["dark"])["plotly"]


# ── Legacy constants (kept for any code that still imports these directly;
#    new code should prefer get_theme_plotly(theme) via make_plotly_layout) ──
PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_PAPER_BG = THEMES["dark"]["plotly"]["paper_bg"]
PLOTLY_PLOT_BG  = THEMES["dark"]["plotly"]["plot_bg"]
PLOTLY_GRID     = THEMES["dark"]["plotly"]["grid"]
PLOTLY_FONT_CLR = THEMES["dark"]["plotly"]["font"]
