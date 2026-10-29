"""Report layer (Modules 7 and 8): builds text/CSV reports of matching shows."""

import csv
import io
import logging
from pathlib import Path

from tvmaze.models import Show

logger = logging.getLogger(__name__)

CSV_COLUMNS = ("name", "genres", "rating", "premiered", "network", "status", "url")


def format_report_text(shows: list[Show], search_term: str, minimum_rating: float) -> str:
    """Return the plain-text report."""
    lines = [
        "TV Show Report",
        "=" * 40,
        f"Search term    : {search_term}",
        f"Minimum rating : {minimum_rating}",
        f"Matching shows : {len(shows)}",
        "",
    ]
    for show in shows:
        lines += [
            f"Name   : {show.name}",
            f"Genres : {show.genre_text}",
            f"Rating : {show.rating_text}",
            "-" * 40,
        ]
    return "\n".join(lines) + "\n"


def _safe_cell(value: object) -> str:
    """Stop spreadsheet apps treating a value as a formula (CSV injection)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def format_report_csv(shows: list[Show]) -> str:
    """Return the report as CSV, one row per show."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for show in shows:
        writer.writerow(
            [
                _safe_cell(show.name),
                _safe_cell("; ".join(show.genres)),
                show.rating if show.rating is not None else "",
                _safe_cell(show.premiered),
                _safe_cell(show.network),
                _safe_cell(show.status),
                _safe_cell(show.url),
            ]
        )
    return buffer.getvalue()


def save_report(
    shows: list[Show], search_term: str, minimum_rating: float, report_file: Path | str
) -> None:
    """Write the plain-text report to report_file.

    Raises OSError if the file cannot be created.
    """
    with open(report_file, "w", encoding="utf-8") as file:
        file.write(format_report_text(shows, search_term, minimum_rating))
    logger.info("%d show(s) written to report %s", len(shows), report_file)
