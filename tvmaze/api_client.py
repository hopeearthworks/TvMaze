"""API layer (Module 5): calls the TVMaze search endpoint."""

import logging

import requests

from tvmaze.models import Show

API_URL = "https://api.tvmaze.com/search/shows"
TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)


def search_shows(search_term):
    """Search TVMaze for shows and return them as a list of Show objects.

    Raises ValueError for an empty search term and requests.RequestException
    if the API cannot be reached or returns an error status.
    """
    if not search_term or not search_term.strip():
        raise ValueError("Search term must not be empty")

    logger.info("Searching TVMaze for '%s'", search_term.strip())
    response = requests.get(API_URL, params={"q": search_term.strip()},
                            timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    results = response.json()

    logger.info("API returned %d result(s)", len(results))
    # Each result looks like {"score": 0.9, "show": {...}}.
    return [Show.from_api(result["show"]) for result in results]
