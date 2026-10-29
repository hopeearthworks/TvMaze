"""Business logic layer (Module 6): ties config, API and filtering together."""

import logging

from tvmaze.api_client import search_shows

logger = logging.getLogger(__name__)


def filter_by_rating(shows, minimum_rating):
    """Return the shows rated at or above minimum_rating (unrated shows are excluded)."""
    matching = [show for show in shows
                if show.rating is not None and show.rating >= minimum_rating]
    logger.info("%d of %d show(s) meet minimum rating %s",
                len(matching), len(shows), minimum_rating)
    return matching


def run(config):
    """Search using the config values and return (all_shows, matching_shows)."""
    shows = search_shows(config.search_term)
    return shows, filter_by_rating(shows, config.minimum_rating)
