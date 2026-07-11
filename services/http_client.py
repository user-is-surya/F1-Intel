"""
F1Intel — Shared HTTP Client

Every API service used to call `requests.get(...)` directly, which opens
a brand-new TCP+TLS connection for every single request and has zero
retry behaviour — one flaky upstream call just hangs for the full
12-second timeout with nothing to show for it. That combination is a
big part of why pages "took forever" to load.

This module gives every service:
  - A pooled requests.Session (connection reuse — no repeated TLS
    handshake cost across the many calls a single page makes).
  - Automatic retries with backoff on transient failures (connection
    errors, 429, 502/503/504) instead of silently giving up once.
  - A shorter, consistent timeout (config.settings.HTTP_TIMEOUT) instead
    of the old blanket 12s.
"""
from __future__ import annotations
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import HTTP_TIMEOUT, HTTP_TOTAL_RETRIES, HTTP_BACKOFF

_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(
            total=HTTP_TOTAL_RETRIES,
            backoff_factor=HTTP_BACKOFF,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _session = s
    return _session


def get_json(url: str, params: dict | None = None, timeout: int | None = None) -> dict | None:
    """GET a URL and return parsed JSON, or None on any failure. Never raises."""
    try:
        r = get_session().get(url, params=params or {}, timeout=timeout or HTTP_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
