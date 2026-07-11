"""
F1Intel — Team Colors & Metadata
Covers 2020–2026+ teams; new teams added dynamically via Jolpica.
"""

# Primary colors keyed by constructor ID (Jolpica/Ergast format)
TEAM_COLORS: dict[str, str] = {
    # 2024/2025/2026 teams
    "red_bull":         "#3671C6",
    "mercedes":         "#00D2BE",
    "ferrari":          "#E8002D",
    "mclaren":          "#FF8000",
    "aston_martin":     "#006F62",
    "alpine":           "#0093CC",
    "williams":         "#64C4FF",
    "rb":               "#6692FF",    # RB / AlphaTauri successor
    "kick_sauber":      "#52E252",    # Kick Sauber → Audi from 2026
    "haas":             "#B6BABD",
    # Legacy names
    "alpha_tauri":      "#4E7C9B",
    "alphatauri":       "#4E7C9B",
    "alfa":             "#C92D4B",
    "alfa_romeo":       "#C92D4B",
    "racing_point":     "#F596C8",
    "renault":          "#FFF500",
    "force_india":      "#F596C8",
    "manor":            "#C82B2B",
    "sauber":           "#9B0000",
    "lotus_f1":         "#B6BABD",
    "marussia":         "#6E0000",
    "caterham":         "#005030",
    "hrt":              "#DDB700",
    "virgin":           "#C82B2B",
    "brawn":            "#80FF00",
    "bmw_sauber":       "#0066CC",
    "toyota":           "#CC1E0F",
    "honda":            "#CC1E0F",
    "super_aguri":      "#CC1E0F",
    "spyker":           "#FF7700",
    "midland":          "#FF6633",
    "jordan":           "#FFFF00",
    "bar":              "#FFCC00",
    "jaguar":           "#006000",
    "minardi":          "#333300",
    "prost":            "#0033CC",
    "arrows":           "#FF6600",
    "benetton":         "#009900",
    "stewart":          "#FFFFFF",
    "tyrrell":          "#003399",
    "lola":             "#CCCC00",
    "mclaren_mercedes": "#FF8700",
    "mclaren_honda":    "#FF8700",
    "constructors":     "#E10600",   # fallback
}

# Short display names for tight UI
TEAM_SHORT: dict[str, str] = {
    "red_bull":      "Red Bull",
    "mercedes":      "Mercedes",
    "ferrari":       "Ferrari",
    "mclaren":       "McLaren",
    "aston_martin":  "Aston Martin",
    "alpine":        "Alpine",
    "williams":      "Williams",
    "rb":            "RB",
    "kick_sauber":   "Kick Sauber",
    "haas":          "Haas",
    "alpha_tauri":   "AlphaTauri",
    "alphatauri":    "AlphaTauri",
    "alfa":          "Alfa Romeo",
    "alfa_romeo":    "Alfa Romeo",
    "racing_point":  "Racing Point",
    "renault":       "Renault",
}

def get_team_color(constructor_id: str) -> str:
    """Return hex color for a constructor, fallback to generic red."""
    key = constructor_id.lower().replace("-", "_").replace(" ", "_")
    return TEAM_COLORS.get(key, "#E10600")

def get_team_short(constructor_id: str) -> str:
    """Return short display name for a constructor."""
    key = constructor_id.lower().replace("-", "_").replace(" ", "_")
    return TEAM_SHORT.get(key, constructor_id.replace("_", " ").title())
