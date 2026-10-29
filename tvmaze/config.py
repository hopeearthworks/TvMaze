"""Configuration layer (Module 6): loads and validates config.json."""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


DEFAULT_OUTPUT_FILE = "tv_report.txt"


@dataclass
class Config:
    search_term: str
    minimum_rating: float
    output_file: str = DEFAULT_OUTPUT_FILE


def load_config(config_path):
    """Load config.json and return a validated Config."""
    try:
        with open(config_path, encoding="utf-8") as config_file:
            raw = json.load(config_file)
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as error:
        raise ConfigError(f"Configuration file is not valid JSON: {error}")

    search_term = str(raw.get("search_term", "")).strip()
    if not search_term:
        raise ConfigError("'search_term' must be a non-empty string")

    try:
        minimum_rating = float(raw.get("minimum_rating", 0))
    except (TypeError, ValueError):
        raise ConfigError("'minimum_rating' must be a number")
    if not 0 <= minimum_rating <= 10:
        raise ConfigError("'minimum_rating' must be between 0 and 10")

    output_file = str(raw.get("output_file", DEFAULT_OUTPUT_FILE)).strip()
    if not output_file:
        raise ConfigError("'output_file' must not be empty")

    config = Config(search_term, minimum_rating, output_file)
    logger.info("Config loaded from %s: %s", config_path, config)
    return config
