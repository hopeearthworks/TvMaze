"""Report layer (Modules 7 and 8): saves matching shows to a text report file."""

import logging

logger = logging.getLogger(__name__)


def save_report(shows, search_term, minimum_rating, report_file):
    """Write the matching shows to report_file.

    Raises OSError if the file cannot be created.
    """
    with open(report_file, "w", encoding="utf-8") as file:
        file.write("TV Show Report\n")
        file.write("=" * 40 + "\n")
        file.write(f"Search term    : {search_term}\n")
        file.write(f"Minimum rating : {minimum_rating}\n")
        file.write(f"Matching shows : {len(shows)}\n\n")
        for show in shows:
            file.write(f"Name   : {show.name}\n")
            file.write(f"Genres : {show.genre_text}\n")
            file.write(f"Rating : {show.rating_text}\n")
            file.write("-" * 40 + "\n")
    logger.info("%d show(s) written to report %s", len(shows), report_file)
