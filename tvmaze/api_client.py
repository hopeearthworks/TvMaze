"""API layer (Module 5): calls the TVMaze API.

Responses are cached in memory for a few minutes, and a request that hits
TVMaze's rate limit (HTTP 429) is retried after a short pause.

TVMaze's search only matches show titles, so genre searches scan the show
index (/shows?page=N) instead. The index is saved to .cache/ for a day.
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

import requests

from tvmaze.models import Show, normalise_genre

API_BASE = "https://api.tvmaze.com"
SEARCH_URL = f"{API_BASE}/search/shows"
SHOW_INDEX_URL = f"{API_BASE}/shows"
TIMEOUT_SECONDS = 10

# Each index page holds up to 250 shows; the oldest IDs include most well-known shows.
INDEX_PAGES = 10
INDEX_TTL_SECONDS = 24 * 60 * 60
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"

CACHE_TTL_SECONDS = 600
CACHE_MAX_ENTRIES = 200
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2.0

logger = logging.getLogger(__name__)

# Maps a request key to (time stored, parsed JSON).
_cache: dict[str, tuple[float, Any]] = {}
# (time loaded, shows) for the genre index.
_show_index: tuple[float, list[Show]] | None = None
_index_lock = threading.Lock()


def clear_cache() -> None:
    """Empty the in-memory caches (used by tests)."""
    global _show_index
    _cache.clear()
    _show_index = None


def get_json(url: str, params: dict[str, Any] | None = None, use_cache: bool = True) -> Any:
    """GET a TVMaze URL and return the parsed JSON, using the cache when possible.

    Raises requests.RequestException if the API cannot be reached or
    returns an error status.
    """
    key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    cached = _cache.get(key) if use_cache else None
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
    if not use_cache:
        return data
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


def get_show_details(show_id: int, max_cast: int = 12) -> dict[str, Any]:
    """Return the cast and next episode for a show.

    Raises requests.RequestException if the API cannot be reached (an
    unknown ID gives a 404 HTTPError).
    """
    data = get_json(f"{SHOW_INDEX_URL}/{int(show_id)}",
                    {"embed[]": ["cast", "nextepisode"]})
    embedded = data.get("_embedded") or {}
    cast = [
        {
            "name": (member.get("person") or {}).get("name"),
            "character": (member.get("character") or {}).get("name"),
            "image": ((member.get("person") or {}).get("image") or {}).get("medium"),
        }
        for member in (embedded.get("cast") or [])[:max_cast]
    ]
    episode = embedded.get("nextepisode")
    next_episode = {
        "name": episode.get("name"),
        "season": episode.get("season"),
        "number": episode.get("number"),
        "airdate": episode.get("airdate"),
    } if episode else None
    return {"id": data.get("id"), "cast": cast, "next_episode": next_episode}


def search_by_genre(genre: str) -> list[Show]:
    """Return shows in the given genre from the show index, highest rated first.

    Raises ValueError for an unknown genre.
    """
    genre = normalise_genre(genre)
    shows = [show for show in load_show_index() if genre in show.genres]
    logger.info("Found %d '%s' show(s) in the show index", len(shows), genre)
    return sorted(shows, key=lambda show: show.rating or 0, reverse=True)


def load_show_index() -> list[Show]:
    """Return the show index from memory, the disk cache or the API (in that order)."""
    global _show_index
    with _index_lock:  # Only one thread downloads the index at a time.
        now = time.time()
        if _show_index and now - _show_index[0] < INDEX_TTL_SECONDS:
            return _show_index[1]

        index_file = CACHE_DIR / "show_index.json"
        shows = _read_index_file(index_file, now)
        if shows is None:
            shows = _download_show_index()
            _write_index_file(index_file, shows, now)
        _show_index = (now, shows)
        return shows


def _download_show_index() -> list[Show]:
    logger.info("Downloading %d page(s) of the TVMaze show index", INDEX_PAGES)
    shows: list[Show] = []
    for page in range(INDEX_PAGES):
        try:
            page_data = get_json(SHOW_INDEX_URL, {"page": page}, use_cache=False)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                break  # Past the last page.
            raise
        shows.extend(Show.from_api(show) for show in page_data)
    logger.info("Show index downloaded: %d show(s)", len(shows))
    return shows


def _read_index_file(index_file: Path, now: float) -> list[Show] | None:
    """Load the saved index if it exists and is less than a day old."""
    try:
        saved = json.loads(index_file.read_text(encoding="utf-8"))
        if now - saved["saved_at"] >= INDEX_TTL_SECONDS:
            return None
        shows = [Show(**show) for show in saved["shows"]]
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.warning("Ignoring unreadable show index cache %s: %s", index_file, error)
        return None
    logger.info("Loaded %d show(s) from %s", len(shows), index_file)
    return shows


def _write_index_file(index_file: Path, shows: list[Show], now: float) -> None:
    try:
        index_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"saved_at": now, "shows": [show.to_dict() for show in shows]}
        index_file.write_text(json.dumps(payload), encoding="utf-8")
    except OSError as error:
        logger.warning("Could not save show index cache %s: %s", index_file, error)
