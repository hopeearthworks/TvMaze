"""Configuration layer (Module 6): loads and validates config.json."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from tvmaze.models import normalise_genre

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


DEFAULT_OUTPUT_FILE = "tv_report.txt"
SEARCH_MODES = ("name", "genre")


@dataclass
class Config:
    search_term: str
    minimum_rating: float
    output_file: str = DEFAULT_OUTPUT_FILE
    search_mode: str = "name"


def load_config(config_path: Path | str) -> Config:
    """Load config.json and return a validated Config."""
    try:
        with open(config_path, encoding="utf-8") as config_file:
            raw = json.load(config_file)
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}") from None
    except json.JSONDecodeError as error:
        raise ConfigError(f"Configuration file is not valid JSON: {error}") from error

    search_mode = str(raw.get("search_mode", "name")).strip().lower()
    if search_mode not in SEARCH_MODES:
        raise ConfigError(f"'search_mode' must be one of: {', '.join(SEARCH_MODES)}")

    search_term = str(raw.get("search_term", "")).strip()
    if not search_term:
        raise ConfigError("'search_term' must be a non-empty string")
    if search_mode == "genre":
        try:
            search_term = normalise_genre(search_term)
        except ValueError as error:
            raise ConfigError(str(error)) from error

    try:
        minimum_rating = float(raw.get("minimum_rating", 0))
    except (TypeError, ValueError):
        raise ConfigError("'minimum_rating' must be a number") from None
    if not 0 <= minimum_rating <= 10:
        raise ConfigError("'minimum_rating' must be between 0 and 10")

    output_file = str(raw.get("output_file", DEFAULT_OUTPUT_FILE)).strip()
    if not output_file:
        raise ConfigError("'output_file' must not be empty")

    config = Config(search_term, minimum_rating, output_file, search_mode)
    logger.info("Config loaded from %s: %s", config_path, config)
    return config
