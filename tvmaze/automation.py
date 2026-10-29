"""Business logic layer (Module 6): ties config, API and filtering together."""

import logging

from tvmaze.api_client import search_by_genre, search_shows
from tvmaze.config import Config
from tvmaze.models import Show

logger = logging.getLogger(__name__)


def search(search_term: str, search_mode: str = "name") -> list[Show]:
    """Search by show title ("name") or by genre ("genre")."""
    if search_mode == "genre":
        return search_by_genre(search_term)
    return search_shows(search_term)


def meets_threshold(show: Show, minimum_rating: float) -> bool:
    """The single rule for "good enough": rated, and at or above the minimum."""
    return show.rating is not None and show.rating >= minimum_rating


def filter_by_rating(shows: list[Show], minimum_rating: float) -> list[Show]:
    """Return the shows rated at or above minimum_rating (unrated shows are excluded)."""
    matching = [show for show in shows if meets_threshold(show, minimum_rating)]
    logger.info(
        "%d of %d show(s) meet minimum rating %s", len(matching), len(shows), minimum_rating
    )
    return matching


def run(config: Config) -> tuple[list[Show], list[Show]]:
    """Search using the config values and return (all_shows, matching_shows)."""
    shows = search(config.search_term, config.search_mode)
    return shows, filter_by_rating(shows, config.minimum_rating)
