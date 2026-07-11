"""
F1Intel — Flag Utilities
Pure Unicode emoji flags. Simple, reliable, no external dependencies.
On Windows 11 these render correctly. On Windows 10 they show as two letters (OS limitation).
"""

from __future__ import annotations

NATIONALITY_ISO: dict[str, str] = {
    "British":"gb","Dutch":"nl","Monegasque":"mc","Spanish":"es","Mexican":"mx",
    "Australian":"au","Canadian":"ca","German":"de","French":"fr","Finnish":"fi",
    "Japanese":"jp","Chinese":"cn","Thai":"th","Danish":"dk","American":"us",
    "Brazilian":"br","Italian":"it","Austrian":"at","Swiss":"ch","Belgian":"be",
    "New Zealander":"nz","Polish":"pl","Argentine":"ar","Venezuelan":"ve",
    "South African":"za","Swedish":"se","Norwegian":"no","Portuguese":"pt",
    "Russian":"ru","Indian":"in","Irish":"ie","Colombian":"co","Czech":"cz",
    "Hungarian":"hu","Bahraini":"bh","Emirati":"ae","Saudi":"sa",
    "Indonesian":"id","Korean":"kr","Singaporean":"sg",
}

COUNTRY_ISO: dict[str, str] = {
    "United Kingdom":"gb","Great Britain":"gb","UK":"gb",
    "Netherlands":"nl","Monaco":"mc","Spain":"es","Mexico":"mx",
    "Australia":"au","Canada":"ca","Germany":"de","France":"fr",
    "Finland":"fi","Japan":"jp","China":"cn","Thailand":"th","Denmark":"dk",
    "USA":"us","United States":"us","Brazil":"br","Italy":"it","Austria":"at",
    "Switzerland":"ch","Belgium":"be","Azerbaijan":"az","Saudi Arabia":"sa",
    "Bahrain":"bh","Qatar":"qa","UAE":"ae","Singapore":"sg","Hungary":"hu",
    "Portugal":"pt","Russia":"ru","South Africa":"za","Argentina":"ar",
    "Sweden":"se","Las Vegas":"us","Miami":"us","New Zealand":"nz",
}

def _to_emoji(iso2: str) -> str:
    """Convert 2-letter ISO code to Unicode flag emoji."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())

# Pre-built emoji maps
_NAT_EMOJI  = {k: _to_emoji(v) for k, v in NATIONALITY_ISO.items()}
_CTRY_EMOJI = {k: _to_emoji(v) for k, v in COUNTRY_ISO.items()}

def get_flag(nationality: str) -> str:
    """Return flag emoji for nationality string."""
    return _NAT_EMOJI.get(nationality) or _CTRY_EMOJI.get(nationality) or ""

def get_country_flag(country: str) -> str:
    """Return flag emoji for country name."""
    return _CTRY_EMOJI.get(country) or _NAT_EMOJI.get(country) or ""

def flag_img(nat_or_country: str, size: int = 20) -> str:
    """Return just the emoji — no img tags, no external URLs, no JS."""
    return get_flag(nat_or_country) or get_country_flag(nat_or_country) or ""

def get_iso(nat_or_country: str) -> str:
    return NATIONALITY_ISO.get(nat_or_country) or COUNTRY_ISO.get(nat_or_country, "")
