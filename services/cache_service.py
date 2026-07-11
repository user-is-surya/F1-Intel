"""
F1Intel — Cache Service
Streamlit-native caching via st.cache_data with per-resource TTLs.
"""

from __future__ import annotations
import streamlit as st
import functools
import time
from config.settings import CACHE_TTL


def cached(resource: str):
    """
    Decorator factory — wraps a function with st.cache_data using
    the TTL defined in settings.CACHE_TTL for that resource key.

    Usage:
        @cached("standings")
        def fetch_standings(season): ...
    """
    ttl = CACHE_TTL.get(resource, 300)

    def decorator(func):
        @st.cache_data(ttl=ttl, show_spinner=False)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def timed_cache(seconds: int):
    """Simple in-memory time-based cache decorator (for non-Streamlit contexts)."""
    def decorator(func):
        _cache: dict = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            if key in _cache:
                result, ts = _cache[key]
                if now - ts < seconds:
                    return result
            result = func(*args, **kwargs)
            _cache[key] = (result, now)
            return result
        return wrapper
    return decorator
