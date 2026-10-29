"""API layer (Module 5): calls the TVMaze API.

Responses are cached in memory for a few minutes, and a request that hits
TVMaze's rate limit (HTTP 429) is retried after a short pause.
"""

import logging
import time
from typing import Any

import requests

from tvmaze.models import Show

API_BASE = "https://api.tvmaze.com"
SEARCH_URL = f"{API_BASE}/search/shows"
TIMEOUT_SECONDS = 10

CACHE_TTL_SECONDS = 600
CACHE_MAX_ENTRIES = 200
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2.0

logger = logging.getLogger(__name__)

# Maps a request key to (time stored, parsed JSON).
_cache: dict[str, tuple[float, Any]] = {}


def clear_cache() -> None:
    """Empty the response cache (used by tests)."""
    _cache.clear()


def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """GET a TVMaze URL and return the parsed JSON, using the cache when possible.

    Raises requests.RequestException if the API cannot be reached or
    returns an error status.
    """
    key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        logger.info("Cache hit: %s", key)
        return cached[1]

    for attempt in range(MAX_RETRIES + 1):
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        if response.status_code == 429 and attempt < MAX_RETRIES:
            logger.warning("TVMaze rate limit reached; retrying in %.0fs", RETRY_DELAY_SECONDS)
            time.sleep(RETRY_DELAY_SECONDS)
            continue
        response.raise_for_status()
        break

    data = response.json()
    if len(_cache) >= CACHE_MAX_ENTRIES:
        _cache.pop(next(iter(_cache)))  # Drop the oldest entry.
    _cache[key] = (time.monotonic(), data)
    return data


def search_shows(search_term: str) -> list[Show]:
    """Search TVMaze show titles and return them as a list of Show objects.

    Raises ValueError for an empty search term and requests.RequestException
    if the API cannot be reached or returns an error status.
    """
    if not search_term or not search_term.strip():
        raise ValueError("Search term must not be empty")

    logger.info("Searching TVMaze for '%s'", search_term.strip())
    results = get_json(SEARCH_URL, {"q": search_term.strip().lower()})
    logger.info("API returned %d result(s)", len(results))
    # Each result looks like {"score": 0.9, "show": {...}}.
    return [Show.from_api(result["show"]) for result in results]
